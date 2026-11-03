package edu.cumt.campusflow.repo;

import edu.cumt.campusflow.model.Site;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SiteRepository extends JpaRepository<Site, String> {
}
