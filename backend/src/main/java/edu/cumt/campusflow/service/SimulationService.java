package edu.cumt.campusflow.service;

import java.util.ArrayList;
import java.util.List;

import org.springframework.stereotype.Service;

/**
 * 逐时段库存递推（与前端、Python 生成脚本同一套公式）。
 *
 * <pre>
 *   S_t     = min(Q_t + A_t, C_t)
 *   Q_(t+1) = Q_t + A_t - S_t
 *   P_t     = min(D_t, I_t + S_t)
 *   I_(t+1) = I_t + S_t - P_t
 *   守恒校验: Q_(t+1) + I_(t+1) = Q_t + I_t + A_t - P_t
 * </pre>
 */
@Service
public class SimulationService {

    /** 单桶仿真结果 */
    public record Row(String bucket, int q, int i, int s, int p, int unmet,
                      boolean riskQ, boolean riskI) {
    }

    /** 输入参数：每桶到件/处理能力/取件需求，以及初值与阈值 */
    public record Inputs(int q0, int i0, int kappaQ, int kappaI,
                         List<String> buckets, List<Integer> arrivals,
                         List<Integer> capacity, List<Integer> pickups) {
    }

    public List<Row> run(Inputs in) {
        int q = in.q0();
        int i = in.i0();
        List<Row> out = new ArrayList<>(in.buckets().size());
        for (int t = 0; t < in.buckets().size(); t++) {
            int a = in.arrivals().get(t);
            int c = in.capacity().get(t);
            int d = in.pickups().get(t);

            int s = Math.min(q + a, c);
            int q2 = q + a - s;
            int p = Math.min(d, i + s);
            int i2 = i + s - p;

            if (q2 + i2 != q + i + a - p) {
                throw new IllegalStateException("守恒式被破坏：" + in.buckets().get(t));
            }
            out.add(new Row(in.buckets().get(t), q2, i2, s, p, d - p,
                    q2 > in.kappaQ(), i2 > in.kappaI()));
            q = q2;
            i = i2;
        }
        return out;
    }

    /** 通道可通行率：约 0.8% 的在架件落地临时堆放，每件占 0.25 m² */
    public double aisleAvailability(int peakI, double channelArea) {
        double pile = peakI * 0.008 * 0.25;
        return Math.max(0, Math.min(1, 1 - pile / channelArea));
    }

    /** 高峰排队时长（分钟）：高峰小时取件量超出自助机吞吐的部分排队 */
    public double queueMinutes(int dailyPickups, int counters, int serviceSeconds, double peakShare) {
        double peakHour = dailyPickups * peakShare;
        double perMin = 60.0 / serviceSeconds;
        double capacity = 60 * perMin * counters;
        double backlog = Math.max(0, peakHour - capacity);
        return backlog / (perMin * counters);
    }
}
