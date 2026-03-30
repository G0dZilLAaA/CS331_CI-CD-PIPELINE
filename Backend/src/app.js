import express  from "express";
import cors     from "cors";
import dotenv   from "dotenv";
import connectDB from "./config/mongodb.js";

import webhookRoutes   from "./routes/webhookRoutes.js";
import dashboardRoutes from "./routes/dashboardRoutes.js";
import pipelineRoutes  from "./routes/pipelineRoutes.js";

dotenv.config();

const app  = express();
const PORT = process.env.PORT || 3000;

// ── Middleware ──────────────────────────────────────
app.use(cors());
app.use(express.json());

// ── Database ────────────────────────────────────────
connectDB();

// ── Health check ────────────────────────────────────
app.get("/", (req, res) => res.send("Server is running"));

// ── Routes ──────────────────────────────────────────
console.log("Setting up routes...");
app.use(webhookRoutes);
app.use(dashboardRoutes);
app.use(pipelineRoutes);

// ── Start ───────────────────────────────────────────
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});