/**
 * Pipeline Logger — Agentic step-by-step logging for the analyze/refine pipeline.
 * Logs each decision point so you can trace exactly what the agent does.
 */

export class PipelineLogger {
    private steps: { step: string; detail: string; ms: number }[] = [];
    private startTime: number;
    private lastTime: number;
    private id: string;

    constructor(mode: string) {
        this.startTime = Date.now();
        this.lastTime = this.startTime;
        this.id = Math.random().toString(36).slice(2, 8);
        console.log(`\n${"=".repeat(70)}`);
        console.log(`🚀 [${this.id}] PIPELINE START — Mode: ${mode}`);
        console.log(`${"=".repeat(70)}`);
    }

    step(name: string, detail: string) {
        const now = Date.now();
        const delta = now - this.lastTime;
        this.lastTime = now;
        this.steps.push({ step: name, detail, ms: delta });
        console.log(`   📌 [${this.id}] ${name} (+${delta}ms)`);
        console.log(`      → ${detail}`);
    }

    decision(name: string, chosen: string, reason: string) {
        const now = Date.now();
        const delta = now - this.lastTime;
        this.lastTime = now;
        this.steps.push({ step: `DECISION: ${name}`, detail: `${chosen} — ${reason}`, ms: delta });
        console.log(`   🔀 [${this.id}] DECISION: ${name} (+${delta}ms)`);
        console.log(`      ✅ Chose: ${chosen}`);
        console.log(`      💡 Reason: ${reason}`);
    }

    skip(name: string, reason: string) {
        console.log(`   ⏭️  [${this.id}] SKIP: ${name}`);
        console.log(`      → ${reason}`);
        this.steps.push({ step: `SKIP: ${name}`, detail: reason, ms: 0 });
    }

    error(name: string, err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        console.log(`   ❌ [${this.id}] ERROR: ${name}`);
        console.log(`      → ${msg}`);
        this.steps.push({ step: `ERROR: ${name}`, detail: msg, ms: 0 });
    }

    end(status: string) {
        const totalMs = Date.now() - this.startTime;
        console.log(`${"─".repeat(70)}`);
        console.log(`🏁 [${this.id}] PIPELINE END — ${status} (${totalMs}ms total, ${this.steps.length} steps)`);
        console.log(`${"─".repeat(70)}\n`);
        return { id: this.id, totalMs, steps: this.steps, status };
    }
}
