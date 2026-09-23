import requests
from decimal import Decimal
from django.conf import settings


class SSLCommerzService:
    """SSLCommerz Payment Gateway Integration Service"""

    SANDBOX_SESSION_URL = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
    LIVE_SESSION_URL = "https://securepay.sslcommerz.com/gwprocess/v4/api.php"

    SANDBOX_VALIDATION_URL = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
    LIVE_VALIDATION_URL = "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"

    def __init__(self, gateway=None):
        # ডেটাবেসে নির্দিষ্ট গেটওয়ে থাকলে সেখান থেকে কী নেবে, নয়তো settings.py থেকে ফলব্যাক করবে
        if gateway and gateway.api_key and gateway.api_secret:
            self.store_id = gateway.api_key
            self.store_passwd = gateway.api_secret
            self.is_sandbox = gateway.gateway_settings.get("is_sandbox", True)
        else:
            self.store_id = getattr(settings, "SSLCOMMERZ_STORE_ID", "testbox")
            self.store_passwd = getattr(settings, "SSLCOMMERZ_STORE_PASS", "qwerty")
            self.is_sandbox = getattr(settings, "SSLCOMMERZ_IS_SANDBOX", True)

        self.session_url = self.SANDBOX_SESSION_URL if self.is_sandbox else self.LIVE_SESSION_URL
        self.validation_url = self.SANDBOX_VALIDATION_URL if self.is_sandbox else self.LIVE_VALIDATION_URL

    def initiate_session(self, payment_data: dict) -> dict:
        """
        SSLCommerz পেমেন্ট সেশন শুরু করে GatewayPageURL রিটার্ন করে
        """
        payload = {
            "store_id": self.store_id,
            "store_passwd": self.store_passwd,
            "total_amount": float(payment_data.get("amount")),
            "currency": payment_data.get("currency", "BDT"),
            "tran_id": payment_data.get("transaction_id"),
            "success_url": payment_data.get("success_url"),
            "fail_url": payment_data.get("fail_url"),
            "cancel_url": payment_data.get("cancel_url"),
            "ipn_url": payment_data.get("ipn_url"),
            # Customer Data
            "cus_name": payment_data.get("customer_name") or "Merchant Owner",
            "cus_email": payment_data.get("customer_email") or "merchant@example.com",
            "cus_add1": payment_data.get("customer_address") or "Dhaka, Bangladesh",
            "cus_city": "Dhaka",
            "cus_country": "Bangladesh",
            "cus_phone": payment_data.get("customer_phone") or "01700000000",
            # Service / Product Info
            "shipping_method": "NO",
            "product_name": payment_data.get("product_name") or "SaaS Plan Subscription",
            "product_category": "Software",
            "product_profile": "non-physical-goods",
        }

        try:
            response = requests.post(self.session_url, data=payload, timeout=20)
            res_data = response.json()

            if res_data.get("status") == "SUCCESS":
                return {
                    "success": True,
                    "gateway_url": res_data.get("GatewayPageURL"),
                    "sessionkey": res_data.get("sessionkey"),
                    "raw_response": res_data,
                }
            return {
                "success": False,
                "error": res_data.get("failedreason", "পেমেন্ট গেটওয়ে সেশন তৈরি ব্যর্থ হয়েছে।"),
                "raw_response": res_data,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_payment(self, val_id: str) -> dict:
        """
        SSLCommerz ভ্যালিডেশন সার্ভার থেকে ট্রানজ্যাকশন ভেরিফাই করা (Anti-Fraud Check)
        """
        params = {
            "val_id": val_id,
            "store_id": self.store_id,
            "store_passwd": self.store_passwd,
            "format": "json",
        }
        try:
            response = requests.get(self.validation_url, params=params, timeout=20)
            res_data = response.json()

            status_val = res_data.get("status", "").upper()
            if status_val in ["VALID", "VALIDATED"]:
                return {
                    "valid": True,
                    "tran_id": res_data.get("tran_id"),
                    "amount": Decimal(str(res_data.get("amount", 0))),
                    "card_type": res_data.get("card_type"),
                    "bank_tran_id": res_data.get("bank_tran_id"),
                    "raw_response": res_data,
                }
            return {
                "valid": False,
                "error": res_data.get("error", "ট্রানজ্যাকশন ভ্যালিডেশন ব্যর্থ হয়েছে।"),
                "raw_response": res_data,
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}