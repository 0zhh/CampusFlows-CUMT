package edu.cumt.campusflow.web;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import edu.cumt.campusflow.model.SimResult;
import edu.cumt.campusflow.model.SimulationRun;
import edu.cumt.campusflow.repo.SimResultRepository;
import edu.cumt.campusflow.repo.SimulationRunRepository;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

/** F1：仿真运行历史 */
@RestController
@RequestMapping("/api/simulations")
public class RunController {

    private final SimulationRunRepository runs;
    private final SimResultRepository results;

    public RunController(SimulationRunRepository runs, SimResultRepository results) {
        this.runs = runs;
        this.results = results;
    }

    @GetMapping
    public List<SimulationRun> list(@RequestParam(required = false) String scenarioId) {
        return (scenarioId == null || scenarioId.isBlank())
                ? runs.findAllByOrderByCreatedAtDesc()
                : runs.findByScenarioIdOrderByCreatedAtDesc(scenarioId);
    }

    @GetMapping("/{id}")
    public Map<String, Object> detail(@PathVariable Long id) {
        SimulationRun run = runs.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "没有这次运行: " + id));
        List<SimResult> rows = results.findByRunIdOrderBySiteIdAscBucketAsc(id);
        return Map.of("run", run, "rows", rows);
    }

    /** 落库一次运行：摘要 + 逐桶结果（调用方给逐桶数据） */
    @PostMapping
    public Map<String, Object> create(@RequestBody Map<String, Object> body) {
        SimulationRun run = new SimulationRun();
        run.scenarioId = String.valueOf(body.getOrDefault("scenarioId", "S2-PEAK"));
        run.seed = ((Number) body.getOrDefault("seed", 42)).intValue();
        run.paramVersion = String.valueOf(body.getOrDefault("paramVersion", "1.0"));
        run.createdAt = LocalDateTime.now();
        run.note = String.valueOf(body.getOrDefault("note", ""));
        run.peakI = ((Number) body.getOrDefault("peakI", 0)).intValue();
        run.riskBuckets = ((Number) body.getOrDefault("riskBuckets", 0)).intValue();
        runs.save(run);

        List<SimResult> saved = new ArrayList<>();
        Object rawRows = body.get("rows");
        if (rawRows instanceof List<?> list) {
            for (Object o : list) {
                if (!(o instanceof Map<?, ?> m)) continue;
                SimResult r = new SimResult();
                r.runId = run.id;
                r.siteId = String.valueOf(m.get("siteId"));
                r.bucket = String.valueOf(m.get("bucket"));
                r.q = num(m.get("q"));
                r.i = num(m.get("i"));
                r.s = num(m.get("s"));
                r.p = num(m.get("p"));
                r.unmet = num(m.get("unmet"));
                r.riskQ = Boolean.parseBoolean(String.valueOf(m.get("riskQ")));
                r.riskI = Boolean.parseBoolean(String.valueOf(m.get("riskI")));
                saved.add(r);
            }
        }
        if (!saved.isEmpty()) results.saveAll(saved);

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("runId", run.id);
        out.put("scenarioId", run.scenarioId);
        out.put("createdAt", run.createdAt);
        out.put("peakI", run.peakI);
        out.put("riskBuckets", run.riskBuckets);
        out.put("rows", saved.size());
        return out;
    }

    private int num(Object o) {
        return o == null ? 0 : ((Number) o).intValue();
    }
}
