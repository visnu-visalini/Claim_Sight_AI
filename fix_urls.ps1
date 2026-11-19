$pages = @(
    "signup.jsx",
    "Dashboard.jsx",
    "NewClaim.jsx",
    "MyClaims.jsx",
    "Profile.jsx",
    "ImageUpload.jsx",
    "DamageResults.jsx",
    "CostEstimation.jsx",
    "ClaimGeneration.jsx",
    "ClaimReview.jsx",
    "AdminDashboard.jsx"
)
$dir = "d:\Claim_Sight_AI\Frontend\src\Pages"
foreach ($page in $pages) {
    $path = Join-Path $dir $page
    if (Test-Path $path) {
        $content = Get-Content $path -Raw
        $updated = $content -replace 'http://127\.0\.0\.1:5000', ''
        Set-Content $path $updated -NoNewline
        Write-Host "Updated: $page"
    }
}