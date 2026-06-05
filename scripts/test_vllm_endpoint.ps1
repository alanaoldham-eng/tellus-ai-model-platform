param(
  [string]$BaseUrl = $env:TELLUS_AI_VLLM_BASE_URL,
  [string]$ApiKey = $env:TELLUS_AI_VLLM_API_KEY,
  [string]$Model = $env:TELLUS_AI_VLLM_GENERAL_MODEL
)

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
  throw "TELLUS_AI_VLLM_BASE_URL is required."
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  throw "TELLUS_AI_VLLM_API_KEY is required."
}

if ([string]::IsNullOrWhiteSpace($Model)) {
  $Model = "Qwen/Qwen3-14B"
}

$base = $BaseUrl.TrimEnd("/")
$headers = @{
  Authorization = "Bearer $ApiKey"
  "Content-Type" = "application/json"
}

Write-Host "Checking models at $base/models ..."
$models = Invoke-RestMethod -Method Get -Uri "$base/models" -Headers $headers
$models | ConvertTo-Json -Depth 8

Write-Host ""
Write-Host "Checking chat completions with model $Model ..."
$body = @{
  model = $Model
  messages = @(
    @{
      role = "system"
      content = "You are a concise Tellus FlowBuilder test assistant."
    },
    @{
      role = "user"
      content = "Reply with exactly: vLLM endpoint is ready."
    }
  )
  temperature = 0.1
  max_tokens = 64
} | ConvertTo-Json -Depth 8

$completion = Invoke-RestMethod `
  -Method Post `
  -Uri "$base/chat/completions" `
  -Headers $headers `
  -Body $body

$completion | ConvertTo-Json -Depth 8
