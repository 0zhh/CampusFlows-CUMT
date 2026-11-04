package edu.cumt.campusflow.web;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import edu.cumt.campusflow.repo.CarrierRepository;
import edu.cumt.campusflow.repo.PickupCodeRepository;
import edu.cumt.campusflow.repo.SiteRepository;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

/** F3：取件码查位置（五表连接） */
@RestController
@RequestMapping("/api/pickup")
public class PickupController {

    private final PickupCodeRepository codes;
    private final SiteRepository sites;
    private final CarrierRepository carriers;

    public PickupController(PickupCodeRepository codes, SiteRepository sites, CarrierRepository carriers) {
        this.codes = codes;
        this.sites = sites;
        this.carriers = carriers;
    }

    @GetMapping("/{code}")
    public Map<String, Object> lookup(@PathVariable String code,
                                      @RequestParam(defaultValue = "NH-TAOYUAN") String siteId) {
        List<Object[]> rows = codes.findDetail(siteId, code);
        if (rows.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "没有这个取件码: " + code);
        }
        Object[] r = rows.get(0);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("code", r[0]);
        out.put("siteId", r[1]);
        sites.findById(siteId).ifPresent(s -> out.put("siteName", s.getName()));
        out.put("parcelId", r[2]);
        String carrierCode = String.valueOf(r[3]);
        out.put("carrierCode", carrierCode);
        out.put("carrier", carriers.findById(carrierCode).map(x -> x.name).orElse(carrierCode));
        out.put("size", r[4]);
        out.put("shelvedAt", r[5]);
        out.put("status", r[6]);
        out.put("shelfNo", r[7]);
        out.put("tier", r[8]);
        out.put("cell", r[9]);
        out.put("zoneId", r[10]);
        return out;
    }

    @GetMapping("/count")
    public Map<String, Object> count(@RequestParam String siteId) {
        return Map.of("siteId", siteId, "codes", codes.countBySiteId(siteId));
    }
}
