# Phase 1: Research - Secure Sandbox & MicroVM Execution

## 1. Problem Statement & Threat Vector Analysis
In AutoJudge, the functionality module (`person_2/functionality/runner.py`) executes third-party submissions. Currently, it calls `subprocess.Popen([sys.executable, script_path])` directly on the host machine.

### Threat Vectors:
1. **Remote Code Execution (RCE)**:
   - Malicious Python script calling `os.system("rm -rf ~")`, installing ransomware, or stealing environment variables (`.env`, `DATABASE_URL`, API keys).
2. **Denial of Service (DoS)**:
   - Fork bombs (`while True: os.fork()`) exhausting host process table (PIDs).
   - CPU starvation (`while True: pass`).
   - Memory exhaustion (allocating large arrays or byte strings) triggering Linux OOM killer on host processes (e.g. killing Postgres or Redis).
3. **Network Egress & Abuse**:
   - Using AutoJudge infrastructure for outbound DDoS, crypto mining pool connections, or scanning local subnets (AWS metadata endpoints `169.254.169.254`, internal databases).
4. **Filesystem Tampering**:
   - Overwriting sibling submission files or tampering with the evaluation harness and test criteria to fake 100% pass rates.

---

## 2. Sandbox Isolation Technologies Comparison

| Technology | Isolation Level | Cold Start Latency | Resource Overhead | Multi-Tenant Suitability | Self-Hosted Feasibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard Docker (`runc`)** | OS-level namespaces & cgroups | ~200 - 400ms | Low | Moderate (shared Linux kernel) | High (runs anywhere Docker runs) |
| **gVisor (`runsc`)** | User-space kernel interception | ~300 - 500ms | Low-Medium | High (syscalls intercepted) | High (Docker runtime plugin) |
| **Firecracker MicroVMs** | Hardware-level virtualization (KVM) | ~5 - 50ms | Very Low | Maximum (independent kernel) | Medium (requires bare metal / KVM support) |
| **E2B Code Interpreter** | Managed Firecracker MicroVMs | ~100 - 150ms | Zero (cloud managed) | Maximum (enterprise-ready) | Low (cloud SaaS API) |

---

## 3. Recommended Architectural Design

To satisfy both **local development/on-prem self-hosting** and **production multi-tenant cloud SaaS**, we implement a **Pluggable Sandbox Provider Pattern**:

```
                       ┌───────────────────────────────┐
                       │     BaseSandboxProvider       │
                       │ (execute_code / execute_file) │
                       └───────────────┬───────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
 ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
 │ DockerSandboxProvider│   │   E2BSandboxProvider │   │ RestrictedFallback   │
 │ (Default Local/Dev)  │   │  (Production Cloud)  │   │   (Unit Tests / CI)  │
 └──────────────────────┘   └──────────────────────┘   └──────────────────────┘
```

### 3.1 Security Hardening Configuration for Docker:
When running in Docker mode, the container MUST be spawned with the following immutable flags:
1. `--network none`: Drops all egress and ingress network interfaces (except loopback `lo`).
2. `--memory 256m --memory-swap 256m`: Hard cap on RAM; process killed if it attempts exceeding limit.
3. `--cpus 1.0`: Hard CPU quota preventing starvation of the host Celery worker.
4. `--pids-limit 64`: Strictly limits concurrent processes to eliminate fork-bomb vulnerabilities.
5. `--read-only`: Root filesystem is read-only. Mounts a transient `tmpfs` at `/sandbox_env` (capped at 50MB) and `/tmp`.
6. `--user 1000:1000`: Runs as unprivileged user, preventing root permissions even if escape occurs.
7. `--cap-drop ALL`: Strips all Linux capabilities (`CAP_SYS_ADMIN`, `CAP_NET_RAW`, etc.).

### 3.2 E2B MicroVM Configuration:
When `SANDBOX_PROVIDER=e2b` and `E2B_API_KEY` is present:
- Code executes inside an ephemeral microVM hosted on E2B's infrastructure.
- Complete hardware virtualization per execution.
- Network access can be toggled per evaluation rubric (e.g. disabled for algorithmic submissions, enabled with domain allowlists for API integration submissions).

---

## 4. Latency & Performance Strategy
- **Container Pooling / Warm Sandboxes**: Keep 1-2 idle sandbox containers warm in the background or use `docker exec` against a running pool container (`sandbox/Dockerfile`) instead of paying container creation overhead on every test case.
- **Batching Test Cases**: Pass the entire test suite into the sandbox in a single execution invocation, returning serialized JSON reports, rather than restarting the container for each individual test case.
