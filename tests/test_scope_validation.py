"""
tests/test_scope_validation.py
Tests for the ScopeValidator module.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from scope_validator import ScopeValidator


class TestPresaleScopeValidator:
    def setup_method(self):
        self.validator = ScopeValidator(scenario="presale")

    # --- In-scope cases ---
    def test_in_scope_product_features(self):
        assert self.validator.is_in_scope("What features does your product have?") is True

    def test_in_scope_use_case(self):
        assert self.validator.is_in_scope("Can you tell me about your use cases for healthcare?") is True

    def test_in_scope_scheduling(self):
        assert self.validator.is_in_scope("I'd like to schedule a demo with your team") is True

    def test_in_scope_company_info(self):
        assert self.validator.is_in_scope("How many customers do you have?") is True

    # --- Out-of-scope: pricing ---
    def test_out_of_scope_price(self):
        assert self.validator.is_in_scope("What is the price of your product?") is False

    def test_out_of_scope_pricing(self):
        assert self.validator.is_in_scope("Can you share your pricing plans?") is False

    def test_out_of_scope_cost(self):
        assert self.validator.is_in_scope("How much does this cost per month?") is False

    def test_out_of_scope_discount(self):
        assert self.validator.is_in_scope("Can I get a 50% discount?") is False

    def test_out_of_scope_quote(self):
        assert self.validator.is_in_scope("Can you give me a quote?") is False

    def test_out_of_scope_invoice(self):
        assert self.validator.is_in_scope("Please send me an invoice") is False

    # --- Out-of-scope: sales closure ---
    def test_out_of_scope_order(self):
        assert self.validator.is_in_scope("I want to place an order") is False

    def test_out_of_scope_contract(self):
        assert self.validator.is_in_scope("Let's sign the contract today") is False

    # --- Redirect responses ---
    def test_redirect_response_english(self):
        response = self.validator.get_redirect_response("en")
        assert isinstance(response, str)
        assert len(response) > 20

    def test_redirect_response_hindi(self):
        response = self.validator.get_redirect_response("hi")
        assert isinstance(response, str)
        assert len(response) > 20

    def test_redirect_response_unknown_lang_defaults_english(self):
        response = self.validator.get_redirect_response("fr")
        assert isinstance(response, str)

    def test_validate_and_redirect_in_scope(self):
        result = self.validator.validate_and_redirect("Tell me about your integrations", "en")
        assert result is None

    def test_validate_and_redirect_out_of_scope(self):
        result = self.validator.validate_and_redirect("What is the price?", "en")
        assert result is not None
        assert isinstance(result, str)


class TestSalesScopeValidator:
    def setup_method(self):
        self.validator = ScopeValidator(scenario="sales")

    def test_in_scope_feature_demo(self):
        assert self.validator.is_in_scope("Can you describe the dashboard features?") is True

    def test_out_of_scope_payment(self):
        assert self.validator.is_in_scope("What are the payment terms?") is False

    def test_out_of_scope_legal(self):
        assert self.validator.is_in_scope("Can you provide legal compliance advice?") is False


class TestMarketingScopeValidator:
    def setup_method(self):
        self.validator = ScopeValidator(scenario="marketing")

    def test_in_scope_case_study(self):
        assert self.validator.is_in_scope("Can you share a customer success story?") is True

    def test_out_of_scope_pricing(self):
        assert self.validator.is_in_scope("What is the pricing for enterprise?") is False

    def test_out_of_scope_confidential(self):
        assert self.validator.is_in_scope("Can you share confidential client data?") is False
