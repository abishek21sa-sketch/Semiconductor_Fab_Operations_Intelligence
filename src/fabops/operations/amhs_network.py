from __future__ import annotations
from fabops.operations.master_data import BAY_SEQUENCE

def amhs_network(seed:int=17) -> dict:
    nodes=[{"id":b,"x":10+(i%4)*27,"y":18+(i//4)*48,"type":"BAY"} for i,b in enumerate(BAY_SEQUENCE)]
    edges=[]
    for i in range(len(BAY_SEQUENCE)-1):
        a,b=BAY_SEQUENCE[i],BAY_SEQUENCE[i+1]
        util=.42+((seed+i*7)%48)/100; queue=(seed+i*3)%7
        edges.append({"from":a,"to":b,"utilization":round(util,3),"queue":queue,"travel_time":round(2.2+util*4.5+queue*.7,2),"type":"PRIMARY"})
    edges += [{"from":"INSPECT","to":"PHOTO","utilization":.81,"queue":5,"travel_time":9.8,"type":"REENTRANT"},
              {"from":"CMP","to":"PHOTO","utilization":.69,"queue":3,"travel_time":7.4,"type":"REENTRANT"}]
    vehicles=[]
    for i in range(8):
        util=.48+((seed+i*11)%47)/100
        vehicles.append({"vehicle_id":f"OHT-{i+1:02d}","utilization":round(min(.98,util),3),"moves":18+(i*5+seed)%31,
                         "state":"SATURATED" if util>.88 else "ACTIVE","current_edge":edges[(i+seed)%len(edges)]["from"]+"→"+edges[(i+seed)%len(edges)]["to"]})
    return {"nodes":nodes,"edges":edges,"vehicles":vehicles,"network_p95_transfer":round(max(x["travel_time"] for x in edges)*1.22,2),
            "congested_edges":sum(x["utilization"]>.75 for x in edges)}
