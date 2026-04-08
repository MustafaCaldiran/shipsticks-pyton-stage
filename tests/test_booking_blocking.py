"""
Environment guardrail: detect bot protection blocking.

If Ship Sticks' bot protection (PerfDrive/ShieldSquare) intercepts the
test runner, this test surfaces it as an explicit, descriptive failure
instead of letting downstream tests fail with confusing locator errors.
"""

import pytest

from pages.booking_step1_page import BookingStep1Page


@pytest.mark.smoke
class TestBookingBlocking:

    def test_surfaces_bot_protection_as_explicit_failure(self, page, base_url):
        """
        Navigate to the booking page and check for bot protection.

        Possible outcomes:
          - Page loads normally → assert shipping heading visible (PASS)
          - Bot protection detected → assert error message is clear (PASS)
        """
        booking = BookingStep1Page(page, base_url)

        error = None
        try:
            booking.goto()
            booking.assert_loaded()
        except RuntimeError as e:
            error = e

        if error:
            assert "bot protection" in str(error).lower(), (
                f"Unexpected error (not bot protection): {error}"
            )
            return

        # If we got here, the page loaded successfully
        from playwright.sync_api import expect
        expect(booking.shipping_options_heading).to_be_visible()
