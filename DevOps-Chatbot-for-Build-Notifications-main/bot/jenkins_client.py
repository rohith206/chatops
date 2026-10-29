import requests

import config

AUTH = (config.JENKINS_USER, config.JENKINS_API_TOKEN)


def _job_path(job: str) -> str:
    return f"{config.JENKINS_URL}/job/{job}"


def last_build(job: str) -> dict:
    r = requests.get(f"{_job_path(job)}/lastBuild/api/json", auth=AUTH, timeout=10)
    r.raise_for_status()
    data = r.json()
    return {
        "job": job,
        "number": data["number"],
        "status": "STARTED" if data["building"] else (data["result"] or "UNKNOWN"),
        "url": data["url"],
        "branch": "",
        "env": "",
    }


def trigger_build(job: str) -> None:
    r = requests.post(f"{_job_path(job)}/build", auth=AUTH, timeout=10)
    r.raise_for_status()
