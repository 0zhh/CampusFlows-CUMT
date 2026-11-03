package edu.cumt.campusflow.web;

import java.util.List;

import edu.cumt.campusflow.model.Site;
import edu.cumt.campusflow.repo.SiteRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;

@RestController
@RequestMapping("/api/sites")
public class SiteController {

    private final SiteRepository sites;

    public SiteController(SiteRepository sites) {
        this.sites = sites;
    }

    @GetMapping
    public List<Site> all() {
        return sites.findAll();
    }

    @GetMapping("/{id}")
    public Site one(@PathVariable String id) {
        return sites.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "站点不存在: " + id));
    }
}
