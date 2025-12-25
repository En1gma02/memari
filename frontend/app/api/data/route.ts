import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";

/**
 * API Route to serve data files from backend/data folder
 * GET /api/data?file=CHAT.txt or file=user-persona.md
 */
export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const file = searchParams.get("file");

    if (!file || !["CHAT.txt", "user-persona.md"].includes(file)) {
        return NextResponse.json(
            { error: "Invalid file parameter. Use CHAT.txt or user-persona.md" },
            { status: 400 }
        );
    }

    try {
        // Navigate from frontend to backend/data
        const dataPath = path.join(process.cwd(), "..", "backend", "data", file);
        const content = await readFile(dataPath, "utf-8");

        return NextResponse.json({ content });
    } catch (error) {
        console.error(`Error reading ${file}:`, error);
        return NextResponse.json(
            { error: `Failed to read ${file}` },
            { status: 500 }
        );
    }
}
