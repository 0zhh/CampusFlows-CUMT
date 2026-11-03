package edu.cumt.campusflow.web;

import java.util.List;
import java.util.Map;
import java.util.stream.IntStream;

import edu.cumt.campusflow.service.SimulationService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 服务端仿真：把逐桶数据送进来，返回 Q/I/S/P 与风险标记 */
@RestController
@RequestMapping("/api/simulation")
public class SimulationController {

    private final SimulationService sim;

    public SimulationController(SimulationService sim) {
        this.sim = sim;
    }

    @SuppressWarnings("unchecked")
    @PostMapping("/run")
    public Map<String, Object> run(@RequestBody Map<String, Object> body) {
        List<String> buckets = (List<String>) body.get("buckets");
        List<Integer> arrivals = ((List<Number>) body.get("arrivals")).stream().map(Number::intValue).toList();
        List<Integer> capacity = ((List<Number>) body.get("capacity")).stream().map(Number::intValue).toList();
        List<Integer> pickups = ((List<Number>) body.get("pickups")).stream().map(Number::intValue).toList();
        int q0 = ((Number) body.getOrDefault("q0", 0)).intValue();
        int i0 = ((Number) body.getOrDefault("i0", 0)).intValue();
        int kappaQ = ((Number) body.getOrDefault("kappaQ", Integer.MAX_VALUE)).intValue();
        int kappaI = ((Number) body.getOrDefault("kappaI", Integer.MAX_VALUE)).intValue();

        var rows = sim.run(new SimulationService.Inputs(q0, i0, kappaQ, kappaI,
                buckets, arrivals, capacity, pickups));

        int peakI = rows.stream().mapToInt(SimulationService.Row::i).max().orElse(0);
        int peakQ = rows.stream().mapToInt(SimulationService.Row::q).max().orElse(0);
        long risk = rows.stream().filter(r -> r.riskI() || r.riskQ()).count();
        double aisle = sim.aisleAvailability(peakI, 144.0);
        double queue = sim.queueMinutes(pickups.stream().mapToInt(Integer::intValue).sum(), 2, 25, 0.18);

        return Map.of(
                "rows", rows,
                "peakI", peakI,
                "peakQ", peakQ,
                "riskBuckets", risk,
                "aisleOkPct", Math.round(aisle * 1000) / 10.0,
                "queueMin", Math.round(queue * 10) / 10.0);
    }

    @PostMapping("/aisle")
    public Map<String, Object> aisle(@RequestBody Map<String, Object> body) {
        int peakI = ((Number) body.getOrDefault("peakI", 0)).intValue();
        double area = ((Number) body.getOrDefault("channelArea", 144.0)).doubleValue();
        return Map.of("aisleOkPct", Math.round(sim.aisleAvailability(peakI, area) * 1000) / 10.0);
    }
}
