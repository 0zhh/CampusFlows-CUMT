package edu.cumt.campusflow.web;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import edu.cumt.campusflow.repo.CarrierRepository;
import edu.cumt.campusflow.repo.ParcelRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** F5：承运商在架统计 */
@RestController
@RequestMapping("/api/stats")
public class StatsController {

    private final ParcelRepository parcels;
    private final CarrierRepository carriers;

    public StatsController(ParcelRepository parcels, CarrierRepository carriers) {
        this.parcels = parcels;
        this.carriers = carriers;
    }

    @GetMapping("/carriers")
    public List<Map<String, Object>> carriers(@RequestParam(defaultValue = "NH-TAOYUAN") String siteId) {
        Map<String, String> names = new LinkedHashMap<>();
        carriers.findAll().forEach(c -> names.put(c.code, c.name));

        List<Map<String, Object>> out = new ArrayList<>();
        for (Object[] row : parcels.countOnShelfByCarrier(siteId)) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("carrierCode", row[0]);
            m.put("carrier", names.getOrDefault(String.valueOf(row[0]), String.valueOf(row[0])));
            m.put("onShelf", ((Number) row[1]).intValue());
            out.add(m);
        }
        return out;
    }
}
