
import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
    try {
        // Adjust path to reach backend/data/ari-life.md from frontend/app/api/...
        // frontend is in d:\Projects\memari\frontend
        // data is in d:\Projects\memari\backend\data
        const filePath = path.join(process.cwd(), "..", "backend", "data", "ari-life.md");

        if (!fs.existsSync(filePath)) {
            return NextResponse.json(
                { error: "Content file not found" },
                { status: 404 }
            );
        }

        const content = fs.readFileSync(filePath, "utf-8");
        return NextResponse.json({ content });
    } catch (error) {
        console.error("Error reading ari-life.md:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
