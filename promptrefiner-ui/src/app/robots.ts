import type { MetadataRoute } from "next";

const BASE_URL = "https://prompttriage.kaelux.dev";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/auth/", "/_next/"],
      },
    ],
    sitemap: `${BASE_URL}/sitemap.xml`,
  };
}
