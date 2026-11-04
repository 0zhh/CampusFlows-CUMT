package edu.cumt.campusflow.repo;

import java.util.List;
import edu.cumt.campusflow.model.Parcel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ParcelRepository extends JpaRepository<Parcel, String> {

    /** 各承运商在架件数（GROUP BY） */
    @Query("""
        select p.carrierCode, count(p)
          from Parcel p
         where p.siteId = :siteId and p.status = 'shelved'
         group by p.carrierCode
         order by count(p) desc
        """)
    List<Object[]> countOnShelfByCarrier(@Param("siteId") String siteId);

    long countBySiteIdAndStatus(String siteId, String status);
}