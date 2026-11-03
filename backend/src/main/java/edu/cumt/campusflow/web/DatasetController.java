package edu.cumt.campusflow.web;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

/**
 * 演示数据集接口。
 *
 * <p>scenarios.json 是 Python 生成脚本的产物（逐桶仿真结果），随 jar 一起打包；
 * 站点与工单走 H2，见 SiteController / WorkOrderController。
 */
@RestController
@RequestMapping("/api")
public class DatasetController {

    private final ObjectMapper mapper = new ObjectMapper();
    private JsonNode scenarios;
    private JsonNode layouts;

    private JsonNode load(String name) {
        try (InputStream in = new ClassPathResource("data/" + name).getInputStream()) {
            String text = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            return mapper.readTree(text);
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "读取数据集失败: " + name, e);
        }
    }

    @GetMapping("/scenarios")
    public synchronized JsonNode scenarios() {
        if (scenarios == null) {
            scenarios = load("scenarios.json");
        }
        return scenarios;
    }

    @GetMapping("/layouts")
    public synchronized JsonNode layouts() {
        if (layouts == null) {
            layouts = load("station_layouts.json");
        }
        return layouts;
    }

    @GetMapping("/layouts/{siteId}")
    public JsonNode layout(@PathVariable String siteId) {
        JsonNode all = layouts();
        for (JsonNode s : all.get("stations")) {
            if (siteId.equals(s.path("station_id").asText())) {
                return s;
            }
        }
        throw new ResponseStatusException(HttpStatus.NOT_FOUND, "没有该站点的布局: " + siteId);
    }
}
