package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"

	"cloud.google.com/go/datastore"
)

const projectId string = "ubc-serverless-ghazal"

var dsClient *datastore.Client

type routing struct {
	active     string
	routing    string
	routing_25 string
	routing_50 string
	routing_75 string
	routing_95 string
}

func init() {
	var err error
	ctx := context.Background()
	dsClient, err = datastore.NewClient(ctx, projectId)
	if err != nil {
		log.Fatalf("datastore.NewClient: %v", err)
	}
}

// The main entrypoint
func getInput(w http.ResponseWriter, r *http.Request) {
	key := datastore.NameKey("routingDecision", "VideoAnalyticsWorkflow", nil)
	r := &routing{}
	if err := dsClient.Get(ctx, key, r); err != nil {
		fmt.Fprintf(w, "failed to get key %+v", key)
		return
	}
	routing := getRouting(r)
	fin := finalRouting(routing)
}

func getRouting(r *routing) []int {
	active := r.active
	var routingStr string
	switch active {
	case "25":
		routingStr = r.routing_25
	case "50":
		routingStr = r.routing_50
	case "75":
		routingStr = r.routing_75
	case "95":
		routingStr = r.routing_95
	default:
		log.Fatalf("invalid active routing %s", active)
	}
	var routing [][]int
	if err := json.Unmarshal([]byte(routingStr), &routing); err != nil {
		log.Fatal(err)
	}
	return routing
}

func finalRouting(routing [][]int) string {
	nonZeroIndices := func(arr []int) {
		var ret []int
		for i, a := range arr {
			if a != 0 {
				ret = append(ret, i+1)
			}
		}
		return ret
	}

	fin := ""

	for _, r := range routing {
		possibleVMs := nonZeroIndices(r)
		if len(possibleVMs) == 0 {
			fn += "0"
		} else {
			allPossibleVMs := append(possibleVMs, 0)
			// TODO: specify weights for random selection
			s := rand.NewSource(time.Now().Unix())
			r := rand.New(s)
			idx := r.Intn(len(allPossibleVMs))
			switch choice := allPossibleVMs[idx]; choice {
			case 0:
				fin += "0"
			default:
				fin += string(64 + choice)
			}
		}
	}
	return fin
}
