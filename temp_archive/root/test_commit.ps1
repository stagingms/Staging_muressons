$body = @{
    dividends_paid = 0
    crisis_severity = 0
    imitation_decay_rate = 0.05
    decisions = @(
        @{
            bu_id = "pharma"
            investment_ratio = 0.25
            capex_allocated = 1000000
            choice_selected = "option_a"
            decision_node_id = "round_1_pharma"
            time_to_decision_seconds = 0
            team_consensus = "majority"
        }
    )
} | ConvertTo-Json -Depth 5

try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/simulations/nonexistent123/commit-turn' -Method POST -Body $body -ContentType 'application/json' -UseBasicParsing -TimeoutSec 10
    Write-Output "STATUS: $($resp.StatusCode)"
    Write-Output "BODY: $($resp.Content)"
} catch {
    Write-Output "HTTP ERROR: $($_.Exception.Response.StatusCode.value__)"
    $stream = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $errorBody = $reader.ReadToEnd()
    Write-Output "ERROR BODY: $errorBody"
}
