# pb-test-driver

Python CLI and MCP server for PowerBuilder test requests and UI checks.
The driver prepares JSON requests and reads correlated JSON reports. It
can wait for a user-started IDE run without an EXE, or start an existing
EXE and check its process outcome. It does not compile PowerScript or
operate the IDE's Run command.

Version 0.2.0 speaks JSON. v0.1.0 used JUnit XML; do not mix that driver
with a JSON framework, or this one with a v0.1.0 host.

```powershell
uv tool install "git+https://github.com/restoresrl/pb-test@v0.2.0#subdirectory=driver"
pb-test --version
```

## Commands

```powershell
pb-test prepare --application myapp --work-dir C:\project --out C:\results\run-001\result.json
# Ask the user to Run the target in the IDE, then:
pb-test wait C:\results\run-001\result.json.request.json --timeout 60
pb-test cleanup C:\results\run-001\result.json.request.json

# Or run a built application:
pb-test run C:\build\orders.exe --application myapp --suite n_suite_orders --out C:\results\run-002\result.json --runtime-version 22.2

pb-test results C:\results\run-002\result.json --json
pb-test runtimes
pb-test serve
```

Use `status` for a nonblocking request check. `prepare` accepts `--ttl`
in seconds (default 1800). `run` accepts `--work-dir`, otherwise it uses
the EXE directory. Application identity is explicit because its object
name can differ from the EXE stem.

The receipt survives server restarts. Reports, receipts and summaries are
evidence, not scratch. A timeout does not cancel or terminate an IDE run.
Cleanup cancels pending requests or releases completed slots; it refuses
active or invalid requests. The EXE command stops only its own process.

The wheel excludes the PowerScript framework. Obtain matching sources
and integrate the host hooks before preparing requests. See the source
repository's [README](https://github.com/restoresrl/pb-test) and its JSON
protocol and application-integration guides. UI tools still need an
interactive Windows desktop and a driver-started EXE; no IDE attachment
is implied by the file-based testing workflow.
