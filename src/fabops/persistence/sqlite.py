from __future__ import annotations
import json, sqlite3
from pathlib import Path
from fabops.ingestion.events import FabEvent

SCHEMA="""
CREATE TABLE IF NOT EXISTS fab_events(
 event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, timestamp REAL NOT NULL,
 lot_id TEXT, tool_id TEXT, body_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_time ON fab_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_lot ON fab_events(lot_id,timestamp);
CREATE TABLE IF NOT EXISTS decisions(
 decision_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 decision_type TEXT NOT NULL, request_json TEXT NOT NULL, response_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scenario_runs(
 run_id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 scenario_name TEXT NOT NULL, result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS supervisor_actions(
 action_id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 decision_id INTEGER, disposition TEXT NOT NULL, actor TEXT NOT NULL, note TEXT, payload_json TEXT NOT NULL
);
"""

class FabRepository:
    def __init__(self, path: str|Path="fabops.db"):
        self.path=str(path); self._init()
    def _connect(self):
        con=sqlite3.connect(self.path); con.row_factory=sqlite3.Row; return con
    def _init(self):
        with self._connect() as con: con.executescript(SCHEMA)
    def append_events(self, events:list[FabEvent]) -> int:
        inserted=0
        with self._connect() as con:
            for e in events:
                cur=con.execute("INSERT OR IGNORE INTO fab_events VALUES(?,?,?,?,?,?)",(
                    e.event_id,e.event_type.value,e.timestamp,e.lot_id,e.tool_id,e.model_dump_json()))
                inserted += cur.rowcount
        return inserted
    def read_events(self, until:float|None=None) -> list[FabEvent]:
        sql="SELECT body_json FROM fab_events"; args=()
        if until is not None: sql += " WHERE timestamp<=?"; args=(until,)
        sql += " ORDER BY timestamp,event_id"
        with self._connect() as con:
            return [FabEvent.model_validate_json(r[0]) for r in con.execute(sql,args)]
    def record_decision(self, decision_type:str, request:dict, response:dict) -> int:
        with self._connect() as con:
            cur=con.execute("INSERT INTO decisions(decision_type,request_json,response_json) VALUES(?,?,?)",
                            (decision_type,json.dumps(request,sort_keys=True),json.dumps(response,sort_keys=True)))
            return int(cur.lastrowid)
    def list_decisions(self, limit:int=50) -> list[dict]:
        with self._connect() as con:
            rows=con.execute("SELECT decision_id,created_at,decision_type,response_json FROM decisions ORDER BY decision_id DESC LIMIT ?",(limit,)).fetchall()
        return [{"decision_id":r[0],"created_at":r[1],"decision_type":r[2],"response":json.loads(r[3])} for r in rows]
    def list_scenarios(self, limit:int=50) -> list[dict]:
        with self._connect() as con:
            rows=con.execute("SELECT run_id,created_at,scenario_name,result_json FROM scenario_runs ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
        return [{"run_id":r[0],"created_at":r[1],"scenario_name":r[2],"result":json.loads(r[3])} for r in rows]
    def record_supervisor_action(self, decision_id:int|None, disposition:str, actor:str, note:str, payload:dict) -> int:
        with self._connect() as con:
            cur=con.execute("INSERT INTO supervisor_actions(decision_id,disposition,actor,note,payload_json) VALUES(?,?,?,?,?)",
                            (decision_id,disposition,actor,note,json.dumps(payload,sort_keys=True)))
            return int(cur.lastrowid)
    def list_supervisor_actions(self, limit:int=50) -> list[dict]:
        with self._connect() as con:
            rows=con.execute("SELECT action_id,created_at,decision_id,disposition,actor,note,payload_json FROM supervisor_actions ORDER BY action_id DESC LIMIT ?",(limit,)).fetchall()
        return [{"action_id":r[0],"created_at":r[1],"decision_id":r[2],"disposition":r[3],"actor":r[4],"note":r[5],"payload":json.loads(r[6])} for r in rows]
    def record_scenario(self, run_id:str, name:str, result:dict):
        with self._connect() as con:
            con.execute("INSERT OR REPLACE INTO scenario_runs(run_id,scenario_name,result_json) VALUES(?,?,?)",
                        (run_id,name,json.dumps(result,sort_keys=True)))
