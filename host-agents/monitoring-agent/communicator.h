#include <iostream>
#include <string>
#include <curl/curl.h>

class communicator
{

public:
    communicator(void)
    {
    }

    int sendprediction(void)
    {
	  CURL *curl;
	  CURLcode res;
	  curl = curl_easy_init();
	  if(curl) {
	    curl_easy_setopt(curl, CURLOPT_URL, "http://192.168.2.153");
	    res = curl_easy_perform(curl);
	    curl_easy_cleanup(curl);
	  }
	  return 0;
	}
};
