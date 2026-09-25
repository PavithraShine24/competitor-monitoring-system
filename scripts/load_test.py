"""Run a real 100-endpoint monitoring load test and write JSON evidence."""
import asyncio, json, time
from pathlib import Path
import httpx

async def probe(client, index):
    started = time.perf_counter(); behavior = index % 10
    url = f"http://127.0.0.1:{9200 + behavior}/health"
    try:
        response = await client.get(url, timeout=2)
        status = "success" if response.is_success else "failed"
        return {"index": index, "status": status, "duration_ms": round((time.perf_counter() - started) * 1000), "http_status": response.status_code, "behavior": behavior}
    except (httpx.HTTPError, TimeoutError) as error:
        return {"index": index, "status": "timeout" if isinstance(error, httpx.TimeoutException) else "failed", "duration_ms": round((time.perf_counter() - started) * 1000), "error": str(error), "behavior": behavior}

async def main():
    started = time.perf_counter()
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    async with httpx.AsyncClient(limits=limits) as client:
        results = await asyncio.gather(*(probe(client, index) for index in range(100)))
    report = {"total_competitors": 100, "checks_executed": len(results), "successful_checks": sum(x["status"] == "success" for x in results), "failed_checks": sum(x["status"] == "failed" for x in results), "timeouts": sum(x["status"] == "timeout" for x in results), "average_check_duration_ms": sum(x["duration_ms"] for x in results) / len(results), "maximum_check_duration_ms": max(x["duration_ms"] for x in results), "total_duration_ms": round((time.perf_counter() - started) * 1000), "observations": results}
    Path("load-test-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "observations"}, indent=2))

if __name__ == "__main__": asyncio.run(main())
