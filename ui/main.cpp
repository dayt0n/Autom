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

//string genCANDisplay(string label,int ID,)

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

vector<double> getTimesforID(int IDtoFind,vector<int> IDs, vector<double> times,int length,int startTime) {
	vector<double> time;
	for(int i = 0; i <= length; i++) { // get count
		if(IDs[i] == IDtoFind) {
			time.push_back(times[i] - startTime);
		}
	}
	return time;
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
	string line;
	int lineCount = 0;
	ifstream myfile(dataFile);
	vector<string> lines;
	while(!myfile.eof()) {
		getline(myfile,line);
		lines.push_back(line);
	}
	myfile.close();
	string CANfile = dataDir + lines[1];
	string decompressedCAN = dataDir + string("decompressed.csv");
	printf("Decompressing CAN data (this may take a while)...\n");
	ifstream src(CANfile,ios::binary); // copy CAN data
	ofstream dst(decompressedCAN,ios::binary);
	dst << src.rdbuf();
	bunzip(CANfile,decompressedCAN); // decompress bz2
	ifstream CANcsv(decompressedCAN);
	vector<double> CANtime;
	vector<int> ID;
	vector <int> DLC;
	vector<string> data;
	string times;
	string IDs;
	string DLCs;
	string datas;
	string descriptor;
	int csvLength = 0;
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
		csvLength++;
	}
	csvLength -= 2;
	CANcsv.close();
	double start = atof(lines[2].c_str());
	double end = atof(lines[3].c_str());
	if(CANtime[0] != start || CANtime[csvLength] != end) {
		printf("Timing mismatch, please consult changes made from data_backup.py\n");
		return -1;
	}
	vector<double> foundTimes = getTimesforID(0x3E9,ID,CANtime,csvLength,start);
	printf("first time for ID %d: %f\n",0x3E9,foundTimes[0]);
	double length = end - start; // all time is in seconds
	printf("length: %f minutes\n",(length/60));
	VideoCapture cap(vidFile);
	if (cap.isOpened() == false) {
		printf("Cannot open file %s\n", vidFile.c_str());
		return -1;
	}
	double fps = cap.get(CV_CAP_PROP_FPS); // dynamic fps adjustment for different cameras
	double timeForFrame = 1.0 / fps;
	printf("Playing at %f frames per second\n",fps);
	string window_name = "Autom Player";
	namedWindow(window_name,WINDOW_NORMAL);
	struct timeval tp;
	gettimeofday(&tp,NULL);
	long int initialTime = tp.tv_sec * 1000 + tp.tv_usec / 1000;
	string now;
	long int thisTime = 0;
	int hours = 0;
	int minutes = 0;
	int seconds = 0;
	int msecs = 0;
	string timer;
	while(true) {
		Mat frame;
		bool bSuccess = cap.read(frame);
		if(bSuccess == false) {
			printf("Found End of video\n");
			break;
		}
		// next: do subtraction on CANtimes to get realtime data, divide by frames per second, and you know what to do from there
		gettimeofday(&tp,NULL);
		thisTime = (tp.tv_sec * 1000 + tp.tv_usec / 1000) - initialTime;
		now = itoa(thisTime);
		hours = (thisTime/1000)/3600;
		minutes = ((thisTime/1000) % 3600)/60;
		seconds = ((thisTime/1000) % 3600) % 60;
		msecs = thisTime - ((hours * 3600 * 1000) + (minutes * 60 * 1000) + (seconds * 1000));
		timer = itoa(hours) + string(":") + itoa(minutes) + string(":") + itoa(seconds) + "." + msectoa(msecs);
		//if(foundTimes[0] >= )
		putText(frame,timer,Point(8,25),CV_FONT_HERSHEY_SIMPLEX,1,Scalar(255,100,255),2);
		imshow(window_name,frame);
		if (waitKey(1000/fps) == 27) {
			printf("Video stopped by user\n");
			break;
		}
	}
	// cleanup
	remove(decompressedCAN.c_str());
	return 0;
}