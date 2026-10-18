import importlib
import os
import tempfile
import unittest
from pathlib import Path

import httpx


class PilotApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        os.environ["CREWS_GIGS_DB"] = str(Path(cls.tempdir.name) / "pilot-test.sqlite3")
        cls.server = importlib.import_module("server")
        cls.server._rate_buckets.clear()

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()
        os.environ.pop("CREWS_GIGS_DB", None)

    async def asyncSetUp(self):
        self.lifespan = self.server.app.router.lifespan_context(self.server.app)
        await self.lifespan.__aenter__()
        self.transport = httpx.ASGITransport(app=self.server.app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://pilot.test")

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.lifespan.__aexit__(None, None, None)

    async def register(self, client, email, name):
        response = await client.post("/api/auth/register", json={
            "name": name,
            "email": email,
            "password": "a-long-test-password-123",
            "discipline": "live production",
            "city": "Lagos",
        })
        self.assertEqual(response.status_code, 201, response.text)
        cookie = response.headers.get("set-cookie", "").lower()
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=strict", cookie)
        return response.json()

    async def test_gig_post_application_close_and_report_permissions(self):
        owner = self.client
        applicant = httpx.AsyncClient(transport=self.transport, base_url="http://pilot.test")
        try:
            owner_data = await self.register(owner, "producer@example.test", "Pilot Producer")
            self.assertTrue(owner.cookies.get("cg_session"))
            csrf = owner_data["csrf_token"]
            payload = {
                "title": "Camera operator for live session",
                "description": "Two-day Lagos shoot.\nBring a camera kit and share a short portfolio.",
                "discipline": "videography",
                "location": "Lagos, Nigeria",
                "engagement": "Paid gig",
                "pay_info": "₦80,000 per day, agreed before booking",
            }
            blocked = await owner.post("/api/gigs", json=payload)
            self.assertEqual(blocked.status_code, 403)
            posted = await owner.post("/api/gigs", json=payload, headers={"X-CSRF-Token": csrf})
            self.assertEqual(posted.status_code, 201, posted.text)
            gig = posted.json()
            self.assertEqual(gig["poster_name"], "Pilot Producer")
            self.assertNotIn("email", gig)

            applicant_data = await self.register(applicant, "crew@example.test", "Pilot Crew")
            self.assertTrue(applicant.cookies.get("cg_session"))
            applicant_csrf = applicant_data["csrf_token"]
            missing_csrf = await applicant.post(f"/api/gigs/{gig['id']}/applications", json={"message": "I have relevant credits and I am available for both shoot days."})
            self.assertEqual(missing_csrf.status_code, 403)
            apply = await applicant.post(f"/api/gigs/{gig['id']}/applications", json={"message": "I have relevant credits and I am available for both shoot days.", "share_email": True}, headers={"X-CSRF-Token": applicant_csrf})
            self.assertEqual(apply.status_code, 201, apply.text)
            duplicate = await applicant.post(f"/api/gigs/{gig['id']}/applications", json={"message": "I have relevant credits and I am available for both shoot days."}, headers={"X-CSRF-Token": applicant_csrf})
            self.assertEqual(duplicate.status_code, 409)
            owner_apps = await owner.get(f"/api/gigs/{gig['id']}/applications")
            self.assertEqual(owner_apps.status_code, 200)
            self.assertEqual(owner_apps.json()["items"][0]["applicant_name"], "Pilot Crew")
            self.assertEqual(owner_apps.json()["items"][0]["applicant_email"], "crew@example.test")
            self.assertEqual((await applicant.get(f"/api/gigs/{gig['id']}/applications")).status_code, 403)

            report = await applicant.post(f"/api/gigs/{gig['id']}/reports", json={"reason": "other", "details": "Duplicate demo report."}, headers={"X-CSRF-Token": applicant_csrf})
            self.assertEqual(report.status_code, 201, report.text)
            self.assertEqual((await applicant.get("/api/moderation/reports")).status_code, 403)
            os.environ["MODERATOR_EMAILS"] = "crew@example.test"
            queue = await applicant.get("/api/moderation/reports")
            self.assertEqual(queue.status_code, 200, queue.text)
            report_id = queue.json()["items"][0]["id"]
            reviewed = await applicant.patch(f"/api/moderation/reports/{report_id}", json={"status":"reviewed","note":"Checked during pilot."}, headers={"X-CSRF-Token": applicant_csrf})
            self.assertEqual(reviewed.status_code, 200, reviewed.text)
            os.environ.pop("MODERATOR_EMAILS", None)
            closed = await owner.patch(f"/api/gigs/{gig['id']}/close", headers={"X-CSRF-Token": csrf})
            self.assertEqual(closed.status_code, 200)
            self.assertEqual((await owner.get("/api/gigs")).json()["items"], [])
        finally:
            await applicant.aclose()

    async def test_auth_validation_security_headers_and_static_file_allowlist(self):
        bad = await self.client.post("/api/auth/register", json={"name": "X", "email": "not-an-email", "password": "short", "discipline": "unknown", "city": "Lagos"})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual((await self.client.get("/health")).headers["x-content-type-options"], "nosniff")
        self.assertEqual((await self.client.get("/server.py")).status_code, 404)
        self.assertEqual((await self.client.get("/instance/pilot.sqlite3")).status_code, 404)
        self.assertEqual((await self.client.get("/docs/../../server.py")).status_code, 404)
        if os.name == "posix":
            self.assertEqual(os.stat(os.environ["CREWS_GIGS_DB"]).st_mode & 0o777, 0o600)
        os.environ["PILOT_INVITE_CODE"] = "pilot-only-code"
        invite_payload = {"name":"Invited Member","email":"invite@example.test","password":"a-long-test-password-123","discipline":"music","city":"Lagos"}
        self.assertEqual((await self.client.post("/api/auth/register", json=invite_payload)).status_code, 403)
        invite_payload["invite_code"] = "pilot-only-code"
        self.assertEqual((await self.client.post("/api/auth/register", json=invite_payload)).status_code, 201)
        os.environ.pop("PILOT_INVITE_CODE", None)
        plan = await self.client.get("/docs/PRODUCT-PLAN.md")
        self.assertEqual(plan.status_code, 200)
        self.assertIn("gig board", plan.text.lower())

    async def test_login_logout_and_missing_csrf(self):
        await self.register(self.client, "member@example.test", "Member One")
        bad_login = await self.client.post("/api/auth/login", json={"email": "member@example.test", "password": "wrong-password"})
        self.assertEqual(bad_login.status_code, 401)
        good_login = await self.client.post("/api/auth/login", json={"email": "member@example.test", "password": "a-long-test-password-123"})
        self.assertEqual(good_login.status_code, 200)
        self.assertTrue(self.client.cookies.get("cg_session"))
        self.assertEqual((await self.client.post("/api/auth/logout")).status_code, 403)
        csrf = good_login.json()["csrf_token"]
        logout = await self.client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
        self.assertEqual(logout.status_code, 204)
        self.assertIsNone((await self.client.get("/api/auth/session")).json()["user"])


if __name__ == "__main__":
    unittest.main()
