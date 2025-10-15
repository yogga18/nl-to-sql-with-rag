from src.db.trx_pertanyaan_repo import get_all_trx_pertanyaan, get_trx_pertanyaan_by_nip, get_trx_pertanyaan_by_id

def get_all_trx_pertanyaan_service(limit: int = 300):
    return get_all_trx_pertanyaan(limit)

def get_trx_pertanyaan_by_nip_service(nip: int):
    return get_trx_pertanyaan_by_nip(nip)

def get_trx_pertanyaan_by_id_service(id: int):
    return get_trx_pertanyaan_by_id(id)