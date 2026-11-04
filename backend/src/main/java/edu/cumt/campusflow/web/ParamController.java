package edu.cumt.campusflow.web;

import java.util.List;
import java.util.Map;

import edu.cumt.campusflow.model.ParamVersion;
import edu.cumt.campusflow.repo.ParamVersionRepository;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

/** F4：参数版本 */
@RestController
@RequestMapping("/api/params")
public class ParamController {

    private final ParamVersionRepository versions;

    public ParamController(ParamVersionRepository versions) {
        this.versions = versions;
    }

    @GetMapping("/versions")
    public List<ParamVersion> list() {
        return versions.findAllByOrderByCreatedAtDesc();
    }

    @GetMapping("/versions/{version}")
    public Map<String, Object> one(@PathVariable String version) {
        ParamVersion v = versions.findById(version)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "没有这个参数版本: " + version));
        return Map.of("version", v.version, "createdAt", v.createdAt,
                "observed", v.observedCnt, "publicCnt", v.publicCnt,
                "assumed", v.assumedCnt, "total", v.totalCnt,
                "payload", v.payload == null ? "[]" : v.payload);
    }
}
