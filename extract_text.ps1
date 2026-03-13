$xmlPath = "$env:TEMP\docx_extract\word\document.xml"
if (Test-Path $xmlPath) {
    $xmlcontent = Get-Content -Path $xmlPath -Raw
    $text = $xmlcontent -replace '<[^>]+>', ' '
    $text = $text -replace '\s+', ' '
    $text | Out-File -FilePath 'C:\Users\DEEPIKA SRI V\OneDrive\Desktop\PPPPPP\rubric_text.txt' -Encoding utf8
} else {
    Write-Error "document.xml not found"
}
