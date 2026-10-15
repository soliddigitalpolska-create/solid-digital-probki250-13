param([int]$ProductId=15,[string]$ProductSlug='notes-pracowni',[string]$ProofName='checkout-http-proof',[string]$CustomerEmail='checkout-workshop@example.invalid')
$ErrorActionPreference = 'Stop'
$origin = 'http://127.0.0.1:8799'
$homePageResponse = Invoke-WebRequest -UseBasicParsing "$origin/" -SessionVariable workshopSession
$product = Invoke-WebRequest -UseBasicParsing "$origin/product/$ProductSlug/" -WebSession $workshopSession
$cart = Invoke-WebRequest -UseBasicParsing "$origin/?add-to-cart=$ProductId" -WebSession $workshopSession
$cartPage = Invoke-WebRequest -UseBasicParsing "$origin/koszyk/" -WebSession $workshopSession
$checkout = Invoke-WebRequest -UseBasicParsing "$origin/zamowienie/" -WebSession $workshopSession
$nonce = [regex]::Match($checkout.Content, 'name="woocommerce-process-checkout-nonce" value="([^"]+)"').Groups[1].Value
if (!$nonce) { throw 'Checkout nonce missing' }
$method = [regex]::Match($checkout.Content, 'name="shipping_method\[0\]"[^>]+value="([^"]+)"').Groups[1].Value
if (!$method -and $ProductId -eq 15) { $method = 'flat_rate:1' }
$form = @{
 billing_first_name='Test'; billing_last_name='Warsztat'; billing_country='PL'; billing_address_1='Testowa 1'; billing_city='Warszawa'; billing_postcode='00-001'; billing_phone='500000000'; billing_email=$CustomerEmail;
 payment_method='bacs'; 'shipping_method[0]'=$method; 'woocommerce-process-checkout-nonce'=$nonce; '_wp_http_referer'='/zamowienie/'; terms='on'; 'terms-field'='1';
}
$result = Invoke-WebRequest -UseBasicParsing "$origin/?wc-ajax=checkout" -Method Post -Body $form -WebSession $workshopSession -Headers @{'X-Requested-With'='XMLHttpRequest'}
$orderResult = $result.Content | ConvertFrom-Json
$orderResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$PSScriptRoot/private/checkout-result.private.json" -Encoding utf8
$expectedTitle=if($ProductId -eq 15){'Notes pracowni'}else{'Konsultacja projektu'}
$proof = [ordered]@{checkedAt=[DateTime]::UtcNow.ToString('o'); product_id=$ProductId; home_status=$homePageResponse.StatusCode; product_status=$product.StatusCode; php_product_note=$product.Content.Contains('Autorska modyfikacja PHP'); cart_status=$cartPage.StatusCode; cart_contains_product=$cartPage.Content.Contains($expectedTitle); checkout_status=$checkout.StatusCode; shipping_method=$method; checkout_result=$orderResult.result; real_charge=$false; real_email=$false; payment_gateway='manual BACS test only'}
$proof | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$PSScriptRoot/proof/$ProofName.json" -Encoding utf8
$proof | ConvertTo-Json -Depth 5
if ($orderResult.result -ne 'success') { throw ($orderResult | ConvertTo-Json -Depth 5) }
