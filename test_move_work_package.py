#!/usr/bin/env python3
"""Offline tests for moving a work package to another project (no network)."""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.client import OpenProjectClient
from src.tools import work_packages


def _client():
    return OpenProjectClient("https://op.example.com", "key")


class UpdateWorkPackageProjectTest(unittest.TestCase):
    def test_client_sends_project_link_with_lock_version(self):
        client = _client()
        client._request = AsyncMock(
            side_effect=[{"lockVersion": 4}, {"id": 983}]  # GET, then PATCH
        )

        asyncio.run(client.update_work_package(983, {"project_id": 12}))

        method, endpoint, payload = client._request.await_args_list[1].args
        self.assertEqual((method, endpoint), ("PATCH", "/work_packages/983"))
        self.assertEqual(payload["lockVersion"], 4)
        self.assertEqual(payload["_links"]["project"], {"href": "/api/v3/projects/12"})

    def test_client_omits_project_link_when_not_moving(self):
        client = _client()
        client._request = AsyncMock(side_effect=[{"lockVersion": 1}, {"id": 983}])

        asyncio.run(client.update_work_package(983, {"subject": "x"}))

        payload = client._request.await_args_list[1].args[2]
        self.assertNotIn("project", payload.get("_links", {}))

    def test_tool_passes_project_id_and_reports_project(self):
        client = AsyncMock()
        client.base_url = "https://op.example.com"
        client.update_work_package.return_value = {
            "id": 983,
            "subject": "s",
            "_embedded": {"project": {"name": "IMAGENPRO"}},
        }
        tool_fn = work_packages.update_work_package

        with patch.object(work_packages, "get_client", return_value=client):
            text = asyncio.run(
                tool_fn(work_packages.UpdateWorkPackageInput(work_package_id=983, project_id=12))
            )

        client.update_work_package.assert_awaited_once_with(983, {"project_id": 12})
        self.assertIn("**Project**: IMAGENPRO", text)

    def test_project_id_must_be_positive(self):
        with self.assertRaises(ValueError):
            work_packages.UpdateWorkPackageInput(work_package_id=1, project_id=0)


if __name__ == "__main__":
    unittest.main()
