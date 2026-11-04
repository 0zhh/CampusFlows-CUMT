package edu.cumt.campusflow.repo;

import java.util.List;
import edu.cumt.campusflow.model.PickupCode;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PickupCodeRepository extends JpaRepository<PickupCode, PickupCode.Key> {

    /** 取件码 → 包裹 → 储位 → 货架 → 货架排，一次 join 取完 */
    @Query("""
        select pc.code, pc.siteId, p.id, p.carrierCode, p.size, p.shelvedAt, p.status,
               sh.bayNo, sl.tier, sl.cellNo, r.zoneId
          from PickupCode pc, Parcel p, Slot sl, Shelf sh, RackRow r
         where pc.parcelId = p.id
           and sl.parcelId = p.id
           and sh.id = sl.shelfId
           and r.id = sh.rowId
           and pc.siteId = :siteId
           and pc.code = :code
        """)
    List<Object[]> findDetail(@Param("siteId") String siteId, @Param("code") String code);

    long countBySiteId(String siteId);
}