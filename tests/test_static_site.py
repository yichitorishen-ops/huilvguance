import unittest

from static_site import relativize_static_paths


class StaticSiteTest(unittest.TestCase):
    def test_relativize_static_paths_for_project_pages(self):
        html = '<link href="/static/app.css"><script src="/static/app.js"></script>'

        self.assertEqual(
            relativize_static_paths(html),
            '<link href="./static/app.css"><script src="./static/app.js"></script>',
        )


if __name__ == "__main__":
    unittest.main()
