"""
Cluster Inspector - Read-only inspection of OpenShift/Kubernetes cluster resources

WARNING: This inspector is READ-ONLY. It will never modify cluster resources.

SECURITY: Password is passed via stdin to avoid exposure in process list.
"""
import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# SSL verification setting - can be disabled for internal CAs
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() == "true"


@dataclass
class ClusterConfig:
    """Configuration for connecting to a cluster"""
    name: str  # e.g., "RHOAI" or "ODH"
    api_server: str
    username: str
    password: str


class ClusterInspector:
    """Read-only inspector for cluster resources"""

    # Default cluster configs - should be overridden with environment variables
    RHOAI_CONFIG = ClusterConfig(
        name="RHOAI",
        api_server=os.getenv("RHOAI_API_SERVER", "https://api.your-rhoai-cluster.example.com:6443"),
        username=os.getenv("RHOAI_USERNAME", "cluster-admin"),
        password=os.getenv("RHOAI_PASSWORD", "")
    )

    ODH_CONFIG = ClusterConfig(
        name="ODH",
        api_server=os.getenv("ODH_API_SERVER", "https://api.your-odh-cluster.example.com:6443"),
        username=os.getenv("ODH_USERNAME", "cluster-admin"),
        password=os.getenv("ODH_PASSWORD", "")
    )

    def __init__(self, cluster_config: ClusterConfig):
        self.config = cluster_config
        self.logged_in = False

    async def login(self) -> bool:
        """
        Login to the cluster using secure password handling.
        
        Password is passed via stdin to avoid exposure in process list (ps aux).
        Returns True if successful.
        """
        # Build command WITHOUT password - password will be passed via stdin
        cmd = [
            "oc", "login",
            "-u", self.config.username,
            "--server", self.config.api_server
        ]
        
        # Add TLS verification flag based on configuration
        if not SSL_VERIFY:
            cmd.append("--insecure-skip-tls-verify=true")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Pass password via stdin (secure - not visible in process list)
        stdout, stderr = await process.communicate(input=f"{self.config.password}\n".encode())

        if process.returncode == 0:
            self.logged_in = True
            return True
        else:
            # Don't log the actual error if it might contain password hints
            error_msg = stderr.decode()
            # Sanitize error message - remove any potential password echoes
            if self.config.password and self.config.password in error_msg:
                error_msg = error_msg.replace(self.config.password, "[REDACTED]")
            print(f"Login failed: {error_msg}")
            return False

    async def _run_oc_command(self, *args) -> Dict[str, Any]:
        """
        Run an oc command and return JSON output

        This is READ-ONLY - only 'get', 'describe', 'logs' commands are allowed
        (plus 'logout' for session cleanup)
        """
        # Safety check - only allow read operations (and logout for cleanup)
        allowed_commands = ['get', 'describe', 'logs', 'whoami', 'version', 'status', 'logout']
        if args[0] not in allowed_commands:
            raise ValueError(f"Command '{args[0]}' is not allowed. This is a READ-ONLY inspector.")

        if not self.logged_in:
            raise RuntimeError("Not logged in to cluster. Call login() first.")

        cmd = ["oc"] + list(args)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return {
                'error': stderr.decode(),
                'returncode': process.returncode
            }

        output = stdout.decode()

        # Try to parse as JSON if output looks like JSON
        if output.strip().startswith('{') or output.strip().startswith('['):
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                pass

        return {'output': output}

    async def get_pods(self, namespace: str = None, label_selector: str = None) -> List[Dict[str, Any]]:
        """Get pods in a namespace"""
        args = ['get', 'pods', '-o', 'json']

        if namespace:
            args.extend(['-n', namespace])
        else:
            args.append('--all-namespaces')

        if label_selector:
            args.extend(['-l', label_selector])

        result = await self._run_oc_command(*args)

        if 'error' in result:
            return []

        return result.get('items', [])

    async def get_pod_logs(self, pod_name: str, namespace: str, container: str = None, tail: int = 100) -> str:
        """Get logs from a pod"""
        args = ['logs', pod_name, '-n', namespace, f'--tail={tail}']

        if container:
            args.extend(['-c', container])

        result = await self._run_oc_command(*args)

        return result.get('output', result.get('error', ''))

    async def describe_pod(self, pod_name: str, namespace: str) -> str:
        """Describe a pod"""
        result = await self._run_oc_command('describe', 'pod', pod_name, '-n', namespace)
        return result.get('output', result.get('error', ''))

    async def get_events(self, namespace: str = None, field_selector: str = None) -> List[Dict[str, Any]]:
        """Get cluster events"""
        args = ['get', 'events', '-o', 'json']

        if namespace:
            args.extend(['-n', namespace])

        if field_selector:
            args.extend(['--field-selector', field_selector])

        result = await self._run_oc_command(*args)

        if 'error' in result:
            return []

        return result.get('items', [])

    async def get_deployments(self, namespace: str) -> List[Dict[str, Any]]:
        """Get deployments in a namespace"""
        result = await self._run_oc_command('get', 'deployments', '-n', namespace, '-o', 'json')

        if 'error' in result:
            return []

        return result.get('items', [])

    async def get_services(self, namespace: str) -> List[Dict[str, Any]]:
        """Get services in a namespace"""
        result = await self._run_oc_command('get', 'services', '-n', namespace, '-o', 'json')

        if 'error' in result:
            return []

        return result.get('items', [])

    async def get_namespaces(self, label_selector: str = None) -> List[Dict[str, Any]]:
        """Get all namespaces"""
        args = ['get', 'namespaces', '-o', 'json']

        if label_selector:
            args.extend(['-l', label_selector])

        result = await self._run_oc_command(*args)

        if 'error' in result:
            return []

        return result.get('items', [])

    async def check_pod_health(self, namespace: str) -> Dict[str, Any]:
        """
        Check health of all pods in a namespace

        Returns summary of pod states
        """
        pods = await self.get_pods(namespace=namespace)

        health = {
            'total': len(pods),
            'running': 0,
            'pending': 0,
            'failed': 0,
            'unknown': 0,
            'crash_looping': 0,
            'image_pull_errors': 0,
            'problems': []
        }

        for pod in pods:
            pod_name = pod['metadata']['name']
            status = pod.get('status', {})
            phase = status.get('phase', 'Unknown')

            if phase == 'Running':
                health['running'] += 1
            elif phase == 'Pending':
                health['pending'] += 1
            elif phase == 'Failed':
                health['failed'] += 1
            else:
                health['unknown'] += 1

            # Check container statuses
            for container_status in status.get('containerStatuses', []):
                waiting = container_status.get('state', {}).get('waiting', {})
                reason = waiting.get('reason', '')

                if 'CrashLoopBackOff' in reason:
                    health['crash_looping'] += 1
                    health['problems'].append({
                        'pod': pod_name,
                        'issue': 'CrashLoopBackOff',
                        'message': waiting.get('message', '')
                    })
                elif 'ImagePullBackOff' in reason or 'ErrImagePull' in reason:
                    health['image_pull_errors'] += 1
                    health['problems'].append({
                        'pod': pod_name,
                        'issue': reason,
                        'message': waiting.get('message', '')
                    })

        return health

    async def find_recent_errors(self, namespace: str, since_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Find recent error events in a namespace

        Args:
            namespace: Namespace to inspect
            since_minutes: Look back this many minutes

        Returns list of error events
        """
        # Get warning and error events
        events = await self.get_events(namespace=namespace)

        errors = []
        for event in events:
            event_type = event.get('type', '')
            if event_type in ['Warning', 'Error']:
                errors.append({
                    'type': event_type,
                    'reason': event.get('reason', ''),
                    'message': event.get('message', ''),
                    'object': event.get('involvedObject', {}).get('name', ''),
                    'count': event.get('count', 1),
                    'lastTimestamp': event.get('lastTimestamp', '')
                })

        return errors

    async def analyze_test_environment(self, namespace: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of test environment health

        This is useful for understanding cluster state when tests fail
        """
        pod_health = await self.check_pod_health(namespace)
        recent_errors = await self.find_recent_errors(namespace)
        deployments = await self.get_deployments(namespace)
        services = await self.get_services(namespace)

        return {
            'cluster': self.config.name,
            'namespace': namespace,
            'pod_health': pod_health,
            'recent_errors': recent_errors,
            'deployment_count': len(deployments),
            'service_count': len(services),
            'has_issues': pod_health['failed'] > 0 or pod_health['crash_looping'] > 0 or len(recent_errors) > 0
        }

    async def logout(self):
        """Logout from cluster (safe to call even if not logged in)"""
        if self.logged_in:
            # Temporarily set logged_in to True to allow the command
            try:
                cmd = ["oc", "logout"]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            except Exception:
                pass  # Ignore logout errors
        self.logged_in = False
