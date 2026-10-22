#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-PackageHomePage: https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware

"""Offline link regression tests; requires the firmware-config dependency PyYAML."""

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest import mock


OVERLAYS_DIR = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "firmware_config",
    OVERLAYS_DIR / "02-firmware-config/root/usr/local/bin/firmware-config.py",
)
firmware_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(firmware_config)


class ServiceLinksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.functions = {}
        for overlay in ("60-app-camera", "61-app-remote-screen"):
            functions_dir = (
                OVERLAYS_DIR / overlay / "root/usr/local/share/firmware-config/functions"
            )
            firmware_config.deep_merge(
                cls.functions, firmware_config.load_functions_from_dir(functions_dir)
            )

    def get_links(self, remote_screen="false", internal="none", usb="none"):
        values = {"remote_screen": remote_screen, "internal": internal, "usb": usb}

        def run_setting(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout=values[cmd[-2]])

        # Exercise the real handler without opening a socket or running device commands.
        handler = firmware_config.FirmwareConfigHandler.__new__(
            firmware_config.FirmwareConfigHandler
        )
        handler.functions = self.functions
        handler.send_json = mock.Mock()
        handler.send_error = mock.Mock()
        with mock.patch.object(firmware_config.subprocess, "run", side_effect=run_setting):
            handler.handle_get_links()

        handler.send_error.assert_not_called()
        handler.send_json.assert_called_once()
        return handler.send_json.call_args.args[0]

    def test_remote_screen_link(self):
        self.assertEqual(
            self.get_links(remote_screen="true"),
            [{"url": "/screen/", "icon": "🖥️", "label": "Remote Screen"}],
        )

    def test_internal_camera_link(self):
        self.assertEqual(
            self.get_links(internal="paxx12"),
            [{"url": "/webcam/", "icon": "📷", "label": "Internal Camera"}],
        )

    def test_usb_camera_link(self):
        self.assertEqual(
            self.get_links(usb="paxx12"),
            [{"url": "/webcam2/", "icon": "📹", "label": "USB Camera"}],
        )

    def test_disabled_services_have_no_links(self):
        self.assertEqual(self.get_links(), [])

    def test_stock_camera_has_no_link(self):
        self.assertEqual(self.get_links(internal="snapmaker"), [])


if __name__ == "__main__":
    unittest.main()
