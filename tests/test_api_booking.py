from __future__ import annotations

import pytest


@pytest.mark.api
@pytest.mark.skip(reason="JavaScript source test is still TODO-backed and capture-dependent.")
class TestApiBooking:
    def test_post_shipments_creates_new_booking(self):
        pass

    def test_delete_or_put_shipments_cancels_booking(self):
        pass

    def test_get_shipments_authenticated_user_can_list_bookings(self):
        pass

    def test_get_shipments_unauthenticated_returns_auth_error(self):
        pass

