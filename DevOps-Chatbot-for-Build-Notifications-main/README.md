# DevOps Chatbot for Build Notifications

A ChatOps bot that sends Jenkins build and deploy status to Slack, and lets your team check or trigger builds from Slack.

**Stack:** Python, Flask, Slack API, Jenkins, Webhooks, Docker

## How it works

```
Jenkins pipeline --(webhook)--> Flask bot --(chat.postMessage)--> Slack channel
Slack /build command ---------> Flask bot --(REST API)----------> Jenkins
```

## Project structure

```
bot/
  app.py             Flask app: webhook + slash command endpoints
  config.py          Loads settings from .env
  formatter.py       Builds the Slack message from a build event
  slack_notifier.py  Posts messages to Slack
  jenkins_client.py  Jenkins REST API (last build, trigger build)
requirements.txt
.env.example
```

## Setup

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Create the Slack app
1. Go to https://api.slack.com/apps, then **Create New App**, then **From scratch**.
2. **OAuth & Permissions**, then **Bot Token Scopes**: add `chat:write`, `chat:write.public`, `commands`.
3. **Install App**, then **Install to Workspace**. Copy the **Bot User OAuth Token** (`xoxb-...`).
4. **Basic Information**, then **Signing Secret**: copy it.
5. Create a public channel (for example `#builds`), copy its **Channel ID**, and run `/invite @DevOps Bot` in it.

### 3. Run Jenkins in Docker
```
docker run -d -p 8080:8080 -p 50000:50000 --name jenkins -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts
docker logs jenkins
```
Open http://localhost:8080, paste the admin password from the logs, install suggested plugins, and create an admin user. Then generate an API token under your username, then **Security**, then **API Token**.

### 4. Configure `.env`
Copy `.env.example` to `.env` and fill in:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_DEFAULT_CHANNEL=C0123ABCDEF     # use the Channel ID, not the name
JENKINS_URL=http://localhost:8080
JENKINS_USER=your-jenkins-user
JENKINS_API_TOKEN=...
WEBHOOK_TOKEN=demo123                 # must match the token in the Jenkinsfile
CHANNEL_MAP=api-deploy=#api-team      # optional per-job channels
```

### 5. Create the Jenkins pipeline
Create a **Pipeline** job named `demo-app` and paste:

```groovy
def notify(status) {
  def body = """{"job":"${env.JOB_NAME}","number":${env.BUILD_NUMBER},"status":"${status}","url":"${env.BUILD_URL}","branch":"main"}"""
  writeFile file: 'payload.json', text: body
  sh "curl -s -X POST ${BOT_URL}/webhook/jenkins -H 'Content-Type: application/json' -H 'X-Webhook-Token: demo123' -d @payload.json"
}

pipeline {
  agent any
  environment { BOT_URL = 'http://host.docker.internal:5000' }
  stages {
    stage('Start') { steps { script { notify('STARTED') } } }
    stage('Build') { steps { sh 'echo building... && sleep 3' } }
  }
  post {
    success { script { notify('SUCCESS') } }
    failure { script { notify('FAILURE') } }
  }
}
```
If Jenkins is not running in Docker, use `http://localhost:5000` as `BOT_URL`.

## Run

```
docker start jenkins
cd bot
python app.py
```
Then click **Build Now** on `demo-app`. You should see a STARTED and then a SUCCESS message in Slack.

### Test the webhook without Jenkins
```
curl -X POST http://localhost:5000/webhook/jenkins -H "X-Webhook-Token: demo123" -H "Content-Type: application/json" -d "{\"job\":\"demo-app\",\"number\":1,\"status\":\"SUCCESS\",\"url\":\"http://localhost:8080\"}"
```

### Slash command (optional)
1. Run `ngrok http 5000` and copy the HTTPS URL.
2. In the Slack app, **Slash Commands**, then **Create New Command**: `/build`, Request URL `https://<ngrok-url>/slack/command`.
3. Use `/build status <job>` or `/build run <job>` in Slack.

## Stop
```
Ctrl+C                 # stop the bot
docker stop jenkins
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/webhook/jenkins` | Receives Jenkins events (needs `X-Webhook-Token`) |
| POST | `/slack/command` | Handles `/build` (verifies the Slack signature) |
| GET | `/health` | Health check |

## Troubleshooting

| Problem | Fix |
|---|---|
| `401` from the webhook | `WEBHOOK_TOKEN` in `.env` doesn't match the Jenkinsfile. Restart the bot after editing `.env`. |
| `channel_not_found` | Use the Channel ID in `SLACK_DEFAULT_CHANNEL`. |
| `not_in_channel` | Run `/invite @DevOps Bot` in the channel. |
| Jenkins can't reach the bot | Use `host.docker.internal` when Jenkins runs in Docker. |
| Slash command times out | ngrok must be running, and its URL changes on every restart. |

## Security

- Keep `.env` out of Git (it is in `.gitignore`).
- The webhook is authenticated with a shared token, and Slack requests are verified with the signing secret.
- If a token is ever exposed, regenerate it in Slack or Jenkins.
