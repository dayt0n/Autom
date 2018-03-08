#include <string>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <unistd.h>
#include <opencv2/opencv.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <sys/time.h>
#include <spawn.h>
#include <signal.h>

using namespace std;
using namespace cv;

string genCANDisplay(string dataStr,vector<int>bits,string label,string units,bool areBitsCombined = FALSE,bool doesHexMatter = FALSE,bool shouldDoMath = FALSE,int op = 0,int coefficient = 0) {
	/* op = operator

		Available operator values
		0 = nothing
		1 = add
		2 = subtract
		3 = multiply
		4 = divide
		5 = percent, coefficient being the maximum value
	*/
	string result;
	unsigned int finalBits = 0;
	dataStr.erase(0,2); // remove leading space and [ charachter
	dataStr.erase(dataStr.size()-1); // remove last ]
	dataStr.erase(remove_if(dataStr.begin(),dataStr.end(),::isspace),dataStr.end()); // remove spaces
	vector<unsigned long> data;
	stringstream ss(dataStr);
	string tok;
	while(getline(ss,tok,','))
		data.push_back(stoi(tok));
	if (bits.size() > 1) {
		if(areBitsCombined) {
			// combine bits
			if(doesHexMatter) {
				// assuming to put them in the order received
				switch(bits.size()) {
					case 8:
						finalBits = (data[bits[0]]<<56) | (data[bits[1]]<<48) | (data[bits[2]]<<40) | (data[bits[3]]<<32) | (data[bits[4]]<<24) | (data[bits[5]]<<16) | (data[bits[6]]<<8) | data[bits[7]];
						break;
					case 7:
						finalBits = (data[bits[0]]<<48) | (data[bits[1]]<<40) | (data[bits[2]]<<32) | (data[bits[3]]<<24) | (data[bits[4]]<<16) | (data[bits[5]]<<8) | data[bits[6]];
						break;
					case 6:
						finalBits = (data[bits[0]]<<40) | (data[bits[1]]<<32) | (data[bits[2]]<<24) | (data[bits[3]]<<16) | (data[bits[4]]<<8) | data[bits[5]];
						break;
					case 5:
						finalBits = (data[bits[0]]<<32) | (data[bits[1]]<<24) | (data[bits[2]]<<16) | (data[bits[3]]<<8) | data[bits[4]];
						break;
					case 4:
						finalBits = (data[bits[0]]<<24) | (data[bits[1]]<<16) | (data[bits[2]]<<8) | data[bits[3]];
						break;
					case 3:
						finalBits = (data[bits[0]]<<16) | (data[bits[1]]<<8) | data[bits[2]];
						break;
					case 2:
						finalBits = (data[bits[0]]<<8) | data[bits[1]];
						break;
					default:
						printf("bits.size() error\n");
						return NULL;
						break;
				}
			} else {
				for(int i = 0; i < bits.size(); i++)
					finalBits += data[bits[i]];
			}
		} else {
			printf("we're going to need more information...\n");
			return NULL;
		}
	} else {
		finalBits = data[bits[0]];
	}
	// now we have finalBits
	if(shouldDoMath) {
		switch(op) {
			case 0:
				printf("shouldDoMath should be set to false if you plan to do no transformation\n");
				break;
			case 1:
				finalBits += coefficient;
				break;
			case 2:
				finalBits -= coefficient;
				break;
			case 3:
				finalBits *= coefficient;
				break;
			case 4:
				finalBits /= coefficient;
				break;
			case 5:
				finalBits = 100 * (finalBits / coefficient);
				break;
			default:
				printf("Invalid operator, doing nothing\n");
				break;
		}
	}
	if (finalBits > 0x0 && finalBits < 0x1EC8) {
		// this is a left turn
		result = label + ": " + to_string(finalBits) + " " + "left";
	} else {
		finalBits = 0xFFFF - finalBits;
		result = label + ": " + to_string(finalBits) + " " + "right";
	}
	return result;
}

/* THIS PART NOT EXACTLY WORKING, MAKES EVERYTHING GO VERY SLOWLY */
string modifyCANDisplayString(int &CANcount,int frameCount,int timeForFrame,vector<double> foundTimes,vector<int>foundPlaces,vector<string> data,vector<int>bits,string label,string units,bool areBitsCombined = FALSE,bool doesHexMatter = FALSE,bool shouldDoMath = FALSE,int op = 0,int coefficient = 0) {
	string text;
	double thisFrame = (frameCount * timeForFrame);
	double nextFrame = ((frameCount + 1) * timeForFrame);
	if (foundTimes[CANcount] < thisFrame) {
		while(CANcount < thisFrame) {
			CANcount++;
			printf("LOTS OF STUFF\n");
		}
	}
	if (CANcount > (data.size() - 2)) {
		printf("ERROR: OUT OF CAN LENGTH\n");
	}
	if(foundTimes[CANcount] >= thisFrame) {
		if (foundTimes[CANcount] < nextFrame) {
			/* do stuff with forming CAN string here */
			printf("%s\n",data[foundPlaces[CANcount]].c_str());
			text = genCANDisplay(data[foundPlaces[CANcount]],bits,label,units,areBitsCombined,doesHexMatter,shouldDoMath,4,100);
			/* end CAN string forming */
			CANcount++;
		}
	}
	return text;
}

extern char **environ;
void run_cmd(string cmd)
{
	pid_t pid;
	char *argv[] = {(char*)"sh", (char*)"-c", (char*)cmd.c_str(), NULL};
	int status;
	status = posix_spawn(&pid, "/bin/sh", NULL, NULL, argv, environ);
	if (status == 0) {
		if (waitpid(pid, &status, 0) != -1) {
		} else {
			perror("waitpid");
		}
	} else {
		printf("posix_spawn: %s\n", strerror(status));
	}
}

void bunzip(string from, string to) { // I apologize for this, no other bz2 decompression method would work :(
	string cmd = "python decompress.py " + from + " " + to;
	run_cmd(cmd);
}

vector<double> getTimesForID(int IDtoFind,vector<int> IDs, vector<double> times,int length,int startTime) {
	vector<double> time;
	for(int i = 0; i <= length; i++) { // get count
		if(IDs[i] == IDtoFind) {
			time.push_back((times[i] - startTime)*666.666666);
		}
	}
	return time;
}

vector<int> getPlacesForID(int IDtoFind,vector<int> IDs,int length,int startTime) {
	vector<int> places;
	for(int i = 0; i <= length; i++) { // get count
		if(IDs[i] == IDtoFind) {
			places.push_back(i);
		}
	}
	return places;
}
string itoa(int n) {
	char str[15];
	String string;
	sprintf(str, "%02d", n);
	string = str;
	return string;
}
string msectoa(int n) {
	char str[15];
	String string;
	sprintf(str, "%03d", n);
	string = str;
	return string;
}

int main(int argc, char* argv[]) {
	string times, IDs, DLCs, datas, descriptor, now, line, speedText;
	vector<int> bitData = {1,2}; // data for speed is located in data packet for ID 0x3E9 in the first two bytes
	vector<double> CANtime;
	vector<int> ID;
	vector <int> DLC;
	vector<string> data;
	vector<string> lines;
	int hours, minutes, seconds, msecs, lineCount, lineNum, frameCount, CANcount = 0;
	if(argc < 2) {
		printf("Incorrect usage\nusage: %s [data directory]\n",argv[0]);
		return -1;
	}
	string dataDir = argv[1];
	if(dataDir[strlen(dataDir.c_str())-1] != '/') {
		dataDir += "/";
	}
	string vidFile = dataDir + string("output.m4v");
	string dataFile = dataDir + string("data_latest.txt");
	ifstream myfile(dataFile);
	while(!myfile.eof()) {
		getline(myfile,line);
		lines.push_back(line);
	}
	myfile.close();
	double start = atof(lines[2].c_str());
	double end = atof(lines[3].c_str());
	double length = end - start; // all time is in seconds

	string CANfile = dataDir + lines[1];
	string decompressedCAN = dataDir + string("decompressed.csv");
	printf("Decompressing CAN data (this may take a while)...\n");
	ifstream src(CANfile,ios::binary); // copy CAN data
	ofstream dst(decompressedCAN,ios::binary);
	dst << src.rdbuf();
	bunzip(CANfile,decompressedCAN); // decompress bz2
	ifstream CANcsv(decompressedCAN);
	printf("Processing %s...\n",CANfile.c_str());
	getline(CANcsv,descriptor,'\n'); // get through first line
	while(!CANcsv.eof()) { // read CSV file
		getline(CANcsv,times,',');
		CANtime.push_back(atof(times.c_str()));
		getline(CANcsv,IDs,',');
		ID.push_back(atoi(IDs.c_str()));
		getline(CANcsv,DLCs,',');
		DLC.push_back(atoi(DLCs.c_str()));
		getline(CANcsv,datas,'\n');
		data.push_back(datas);
	}
	int csvLength = (CANtime.size() - 2);
	CANcsv.close();

	if(CANtime[0] != start || CANtime[csvLength] != end) {
		printf("Timing mismatch, please consult changes made from data_backup.py\n");
		return -1;
	}
	vector<double> foundTimes = getTimesForID(0x1E5,ID,CANtime,csvLength,start); // speed ID for chevy volt is 0x3E9

	vector<int> foundPlaces = getPlacesForID(0x1E5,ID,csvLength,start);
	printf("length: %f minutes\n",(length/60));
	VideoCapture cap(vidFile);
	if (cap.isOpened() == false) {
		printf("Cannot open file %s\n", vidFile.c_str());
		return -1;
	}
	double fps = cap.get(CV_CAP_PROP_FPS); // dynamic fps adjustment for different cameras
	double timeForFrame = 1000 / fps;
	printf("Playing at %f|%f frames per second\n",fps,timeForFrame);
	string window_name = "Autom Player";
	namedWindow(window_name,CV_WINDOW_NORMAL);
	long int currentTime = 0;
	while(true) {
		Mat frame;
		bool bSuccess = cap.read(frame);
		if(bSuccess == false) {
			printf("End of video\n");
			break;
		}
		currentTime = cap.get(CV_CAP_PROP_POS_MSEC);
		frameCount = cap.get(CV_CAP_PROP_POS_FRAMES);
		// make sure no CAN messages are left behind
		while(foundTimes[CANcount] < currentTime) // must convert to int as to not have video/data lag
			CANcount++; // instead of this should have an algorithm to get average time between messages and then add to CANcount accordingly
		if (CANcount > csvLength) {
			printf("ERROR: OUT OF CAN LENGTH\n");
			break;
		}
		if(currentTime <= foundTimes[CANcount] && foundTimes[CANcount] < (currentTime + (int)timeForFrame)) {
			// do stuff with forming CAN string here 
			printf("foundTimes[%d]: %f | currentTime: %ld | nextFrame: %ld\n",CANcount,foundTimes[CANcount],currentTime,currentTime + (int)timeForFrame);
			speedText = genCANDisplay(data[foundPlaces[CANcount]],bitData,"Steer","steer units",TRUE,TRUE);
			// end CAN string forming 
			CANcount++; // let program know to wait for the next one
		}
		//speedText = modifyCANDisplayString(CANcount,frameCount,timeForFrame,foundTimes,foundPlaces,data,bitData,"Speed","mph",TRUE,TRUE,TRUE,4,100);
		putText(frame,speedText,Point(250,25),CV_FONT_HERSHEY_SIMPLEX,1,Scalar(255,0,0),2);
		putText(frame,currentTime,Point(8,25),CV_FONT_HERSHEY_SIMPLEX,1,Scalar(255,100,255),2);
		imshow(window_name,frame);
		if (waitKey((int)timeForFrame) == 27) {
			printf("Video stopped by user\n");
			break;
		}
	}
	// cleanup
	remove(decompressedCAN.c_str());
	return 0;
}