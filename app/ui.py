from fastapi.responses import HTMLResponse
from fastapi import APIRouter
router = APIRouter()



from fastapi.responses import HTMLResponse
from fastapi import APIRouter
router = APIRouter()

@router.get("/review-pr", response_class=HTMLResponse)
def review_pr_form():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>Analyze PR</title>
    <style>
      body {
        background: #f6f8fa;
        min-height: 100vh;
        margin: 0;
        font-family: 'Segoe UI', Arial, sans-serif;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .center-box {
        background: #fff;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        min-width: 340px;
        width: 100%;
        max-width: 600px;
      }
      h1 {
        text-align: center;
        color: #2596be;
        margin-bottom: 1.5rem;
      }
      form {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
      }
      .form-group {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        width: 100%;
      }
      label {
        font-weight: 800;
        color: #222;
        margin-bottom: 0.4rem;
        text-align: left;
      }
      input[type="text"], input[type="number"], input[type="password"] {
        width: 100%;
        padding: 0.6rem 0.8rem;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(37,99,235,0.08);
        font-size: 1rem;
        outline: none;  
        transition: border 0.2s;
        box-sizing: border-box;
      }
      input:focus {
        border: 1.5px solid #2563eb;
      }
      button {
        background: #1e81b0;
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 0;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(37,99,235,0.10);
        transition: background 0.2s;
        width: 100%;
        margin-top: 0.5rem;
      }
      button:hover {
        background: #0a538d;
      }
      .api-buttons {
        display: flex;
        gap: 1rem;
        margin-top: 1.2rem;
        justify-content: center;
      }
      #result, #status, #review-result {
        margin-top: 1.2rem;
        text-align: center;
        font-size: 1.05rem;
        word-break: break-all;
      }
    </style>
    </head>
    <body>
    <div class="center-box">
      <h1>AI-powered Code Review System</h1>
      <form id="analyzeForm">
        <div class="form-group">
          <label for="repo_url">REPO URL *</label>
          <input type="text" id="repo_url" name="repo_url" placeholder="Eg: https://github.com/Himangshu1086/ai-agent/pull/3" required>
        </div>
        <div class="form-group">
          <label for="pr_number">PR NUMBER *</label>
          <input type="number" id="pr_number" name="pr_number" placeholder="Eg. 3" required>
        </div>
        <div class="form-group">
          <label for="github_token">GITHUB TOKEN *</label>
          <input type="password" id="github_token" name="github_token" placeholder="ghp_hb***" required>
        </div>
        <button type="submit">START</button>
      </form>
      <div id="result"></div>
      <div class="api-buttons">
        <button id="statusBtn" type="button" disabled>Check Status</button>
        <button id="reviewBtn" type="button" disabled>Get Result</button>
      </div>
      <div id="status"></div>
      <div id="review-result"></div>
    </div>
    <script>
      let lastTaskId = null;

      document.getElementById('analyzeForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const form = e.target;
        const data = {
          repo_url: form.repo_url.value,
          pr_number: parseInt(form.pr_number.value, 10),
          github_token: form.github_token.value
        };
        document.getElementById('result').textContent = 'Submitting...';
        document.getElementById('status').textContent = '';
        document.getElementById('review-result').textContent = '';

        try {
          const response = await fetch('/analyze-pr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          const result = await response.json();
          document.getElementById('result').textContent = 'Task ID: ' + result.task_id;
          lastTaskId = result.task_id;
          document.getElementById('statusBtn').disabled = false;
          document.getElementById('reviewBtn').disabled = false;
        } catch (err) {
          document.getElementById('result').textContent = 'Error: ' + err;
        }
      });

      document.getElementById('statusBtn').addEventListener('click', async function() {
        if (!lastTaskId) return;
        const statusDiv = document.getElementById('status');
        statusDiv.textContent = 'Checking status...';
        statusDiv.style.color = '';
        statusDiv.style.fontWeight = '';
        try {
          const response = await fetch('/status/' + lastTaskId);
          const result = await response.json();
          let color = '';
          let weight = '600';
          if (result.status === 'PENDING') {
            color = '#f59e42'; // orange-600
          } else if (result.status === 'SUCCESS' || result.status === 'completed') {
            color = '#22c55e'; // green-500
          } else if (result.status === 'FAILURE' || result.status === 'failed') {
            color = '#ef4444'; // red-500
          } else {
            color = '#222';
            weight = '400';
          }
          statusDiv.textContent = 'Status: ' + result.status;
          statusDiv.style.color = color;
          statusDiv.style.fontWeight = weight;
        } catch (err) {
          statusDiv.textContent = 'Error: ' + err;
          statusDiv.style.color = '#ef4444';
          statusDiv.style.fontWeight = '600';
        }
      });

      document.getElementById('reviewBtn').addEventListener('click', async function() {
        if (!lastTaskId) return;
        document.getElementById('review-result').textContent = 'Fetching result...';
        try {
          const response = await fetch('/results/' + lastTaskId);
          const result = await response.json();
          document.getElementById('review-result').textContent = 'Result: ' + JSON.stringify(result, null, 2);
        } catch (err) {
          document.getElementById('review-result').textContent = 'Error: ' + err;
        }
      });
    </script>
    </body>
    </html>
    """