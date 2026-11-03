package edu.cumt.campusflow;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import edu.cumt.campusflow.service.SimulationService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class SimulationServiceTest {

    private final SimulationService sim = new SimulationService();

    @Test
    @DisplayName("三个手算案例：处理能力、积压结转、取件结转")
    void handCalculatedCases() {
        var in = new SimulationService.Inputs(
                0, 100,
                1000, 1000,
                List.of("08:00", "08:30", "09:00"),
                List.of(50, 200, 30),
                List.of(100, 100, 100),
                List.of(40, 60, 200));

        var rows = sim.run(in);

        // t0: S=min(0+50,100)=50, Q2=0, P=min(40,100+50)=40, I2=110
        assertThat(rows.get(0).s()).isEqualTo(50);
        assertThat(rows.get(0).q()).isZero();
        assertThat(rows.get(0).p()).isEqualTo(40);
        assertThat(rows.get(0).i()).isEqualTo(110);

        // t1: S=min(0+200,100)=100, Q2=100, P=min(60,110+100)=60, I2=150
        assertThat(rows.get(1).s()).isEqualTo(100);
        assertThat(rows.get(1).q()).isEqualTo(100);
        assertThat(rows.get(1).i()).isEqualTo(150);

        // t2: Q 还有 100 未处理，本桶到 30，处理能力 100 → S=100；
        //     可交付 150(I) + 100(S) = 250，需求 200 全部满足
        assertThat(rows.get(2).s()).isEqualTo(100);
        assertThat(rows.get(2).p()).isEqualTo(200);
        assertThat(rows.get(2).unmet()).isZero();
        assertThat(rows.get(2).i()).isEqualTo(50);
    }

    @Test
    @DisplayName("守恒式在任意随机输入下都成立")
    void conservationHoldsForRandomInputs() {
        java.util.Random rnd = new java.util.Random(42);
        for (int round = 0; round < 50; round++) {
            int n = 1 + rnd.nextInt(30);
            List<String> buckets = java.util.stream.IntStream.range(0, n)
                    .mapToObj(i -> "T" + i).toList();
            List<Integer> arrivals = java.util.stream.IntStream.range(0, n)
                    .mapToObj(i -> rnd.nextInt(400)).toList();
            List<Integer> capacity = java.util.stream.IntStream.range(0, n)
                    .mapToObj(i -> 1 + rnd.nextInt(300)).toList();
            List<Integer> pickups = java.util.stream.IntStream.range(0, n)
                    .mapToObj(i -> rnd.nextInt(400)).toList();

            int q0 = rnd.nextInt(50);
            int i0 = rnd.nextInt(500);
            var rows = sim.run(new SimulationService.Inputs(q0, i0, 10_000, 10_000,
                    buckets, arrivals, capacity, pickups));

            int q = q0, i = i0;
            for (int t = 0; t < n; t++) {
                var r = rows.get(t);
                assertThat(r.q() + r.i())
                        .as("第 %d 桶守恒", t)
                        .isEqualTo(q + i + arrivals.get(t) - r.p());
                q = r.q();
                i = r.i();
            }
        }
    }

    @Test
    @DisplayName("通道可通行率与排队时长随负载单调变化")
    void metricsBehaveMonotonically() {
        double low = sim.aisleAvailability(1_000, 144);
        double high = sim.aisleAvailability(16_000, 144);
        assertThat(low).isGreaterThan(high);
        assertThat(high).isBetween(0.0, 1.0);

        double oneCounter = sim.queueMinutes(2_644, 1, 25, 0.18);
        double twoCounters = sim.queueMinutes(2_644, 2, 25, 0.18);
        assertThat(oneCounter).isGreaterThan(twoCounters);
    }
}
