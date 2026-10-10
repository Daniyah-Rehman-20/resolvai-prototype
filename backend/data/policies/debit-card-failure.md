# Debit card failures
Reviewed: 2026-10-09. Jurisdiction: India. Informational guidance; applicability must be confirmed from transaction evidence.

Source: RBI/2019-20/67, 20 September 2019. https://www.rbi.org.in/Commonperson/english/Scripts/Notification.aspx?Id=3074
For domestic debit-card merchant payments with a debit but no merchant confirmation (PoS or e-commerce), auto-reversal is T+5; delay compensation is INR 100 per day thereafter. ATM debit without cash has the same T+5 outer limit and daily compensation. Card-to-card transfers without beneficiary credit instead have T+1 reversal if credit is not effected.

## Product investigation guidance
Identify ATM, merchant purchase, or transfer before selecting a rule. Confirm posted debit versus authorization hold with the issuer. Never infer a successful refund from an internal case status. Never collect a PIN, CVV, OTP, or full card number.
