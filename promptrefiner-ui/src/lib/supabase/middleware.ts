import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Refreshes the Supabase session and enforces authentication.
 * Unauthenticated users visiting protected routes are redirected to /login.
 */
export async function updateSession(request: NextRequest) {
    let supabaseResponse = NextResponse.next({
        request,
    });

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
        {
            cookies: {
                getAll() {
                    return request.cookies.getAll();
                },
                setAll(cookiesToSet) {
                    cookiesToSet.forEach(({ name, value }) =>
                        request.cookies.set(name, value),
                    );
                    supabaseResponse = NextResponse.next({
                        request,
                    });
                    cookiesToSet.forEach(({ name, value, options }) =>
                        supabaseResponse.cookies.set(name, value, options),
                    );
                },
            },
        },
    );

    // Refresh the session — this is critical for keeping auth alive
    const { data: { user } } = await supabase.auth.getUser();

    // Public routes that don't require authentication
    const publicPaths = ["/login", "/auth/callback", "/pricing"];
    const pathname = request.nextUrl.pathname;
    const isPublicRoute = publicPaths.some((path) => pathname.startsWith(path));
    const isApiRoute = pathname.startsWith("/api/");

    // Redirect unauthenticated users to /login (skip API routes — they return 401)
    if (!user && !isPublicRoute && !isApiRoute) {
        const loginUrl = request.nextUrl.clone();
        loginUrl.pathname = "/login";
        return NextResponse.redirect(loginUrl);
    }

    // If authenticated user visits /login, redirect them to /
    if (user && pathname === "/login") {
        const homeUrl = request.nextUrl.clone();
        homeUrl.pathname = "/";
        return NextResponse.redirect(homeUrl);
    }

    return supabaseResponse;
}
