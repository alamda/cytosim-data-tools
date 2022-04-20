/**/
#include <iostream>
#include <fstream>
#include <stdio.h>
#include<math.h>
//#include <cmath>
using namespace std;

int main(int argc, char *argv[]){

     if(argc!=2){
                cout << "Input format: program inputfile" << endl;
                exit(0);
                }

        ifstream input(argv[1]);
        if(! input){
                cout << argv[1] << " could not be opened." << endl;
                exit(0);
                }
        ofstream output("q6.dat");
        if(! output){
                cout << "q6.dat could not be opened." << endl;
                exit(0);
                }

        cout << "You will need to enter a series of values for the program to proceed." << endl;

        double cutoff;
        cout << "Please enter a cutoff to build the nearest neighbor list for actin:\n>";
        cin >> cutoff;
        while (cutoff > 5 || cutoff < 0){
                cout << "Invalid choice, try again:";
                cin >> cutoff;
                if(cin.fail()){
                        cin.clear();
                        char c;
                        cin >> c;
                        }
                }
//definie array for neighbour list and make them zero 
		double neighbor[2][200][210]={0};
		double actin[210][8]={0};
                int  i,j,atoms=200, num_actin, timestep,counter=0;
		double id,type;
		double time, x, y, dx, dy, dirx, diry, xi, xj, yi, yj, aix, aiy, anum, Qparam1, Qparam2, dij,length;
 		char name[256], title[256];



	while(true) {
		num_actin=0;
                for(int i=0; i<200; i++){
                        for(j=0; j<200; j++){
                                neighbor[1][i][j]=100;
                                neighbor[0][i][j]=1000;
                                }

}
              //read trj from here
                input.getline(name, 256);
                if(input.eof()) break;
                input.getline(name, 256);
                sscanf(name ,name, "%d", &timestep);
                input.getline(name, 256);
	        sscanf(name ,name, "%lf", &time);
                input.getline(name, 256);
		input.getline(name, 256);		
		input.getline(name, 256);

		counter++; //count the number of frames
		for(i=0; i<atoms; i++){
                        input.getline(name, 256);
                        sscanf(name, "%lf %lf %lf %lf %lf %lf %lf", &type, &id,&length, &x, &y, &dirx, &diry);
                        actin[num_actin][1]=x;
                        actin[num_actin][2]=y;
                        actin[num_actin][3]=x+0.125*dirx;
			actin[num_actin][4]=y+0.125*diry;
			actin[num_actin][5]=dirx;
                        actin[num_actin][6]=diry;
			//cout<< actin[num_actin][1]<< " "<<actin[num_actin][3]<<" "<< actin[num_actin][5] <<endl; 	
                        num_actin++;
			 }
	        input.getline(name, 256);
		//int imax=0, n=0;
		//build the list of nearest neighbour 
		 for(int i=0; i<atoms; i++){
                        xi = actin[i][3];
                        yi = actin[i][4];
			int imax=0;
                        for(int j=0; j<atoms;j++){
                                if(j==i) {continue;}
                                xj = actin[j][3];
                                yj = actin[j][4];
                                dx=xj-xi;
                                dy=yj-yi;
				dij=sqrt(dx*dx+dy*dy);
                                if(dij>cutoff) {continue;}
                           //     double tmp=0;
				//for( n=0; n<20;n++){
                                  //      if(tmp<neighbor[1][n][i]){
                                   //             tmp=neighbor[1][n][i];
                                    //            imax=n;
                                     //           }
                                      //  }
                                //if(dij>neighbor[1][imax][i]) {continue;}
				//else{
                                        neighbor[1][imax][i]=dij;
                                        neighbor[0][imax][i]=j;
                                //        }
                             //   cout<< i << " " <<j<<endl;
				        imax++;
                                }
				if(imax!=0)
				{actin[i][7]=imax;
			//	cout << i << " " << imax << endl;
				}
				else
				actin[i][7]=0;
                        }// end of build the list of nearest neighbour

//calculate the q6 order 
		int ajID=100;
		double ajx, ajy, aix, aiy;
		double theta=0;  
		for(i=0; i< atoms; i++){
                        Qparam1=0;
			Qparam2=0;
			double Qparam=0;
                        aix=actin[i][5];
                        aiy=actin[i][6];
			int imax=int(actin[i][7]);
			if(imax !=0){
                        for(j=0; j<imax; j++){
                                ajID = int(neighbor[0][j][i]);
                                ajx=actin[ajID][5];
                                ajy=actin[ajID][6];
//				cout << ajID<< " " <<ajx <<" " << ajy<< endl;
				theta= acos((aix*ajx+aiy*ajy)/(sqrt(aix*aix+aiy*aiy)*sqrt(ajx*ajx+ajy*ajy)));
				//cout << aix*ajx+aiy*ajy << " " << theta << endl;
				Qparam1 = Qparam1 + cos(theta);
				Qparam2	= Qparam2 + sin(theta);
                                }
				Qparam=Qparam*1.0/imax;
				Qparam1 = Qparam1*1.0/imax;
				Qparam2 = Qparam2*1.0/imax;
				}
				
                        output << i << " "<< imax <<" "<<  Qparam1 <<" "<< Qparam2 << endl; //output
                }

}}
 
