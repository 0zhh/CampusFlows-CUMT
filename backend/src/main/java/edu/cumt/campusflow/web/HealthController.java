package edu.cumt.campusflow.web;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {
    @GetMapping("/api/health")
    public Map<String, Object> health() {
        return Map.of("status", "ok", "app", "campusflow", "version", "1.0.0");
    }
}
