/**/
#include <iostream>
#include <fstream>
#include <stdio.h>
#include<math.h>
#define PI 3.14159265
#include <cmath>
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
        ofstream output("grtheta.dat");
        if(! output){
                cout << "grtheta.dat could not be opened." << endl;
                exit(0);
                }

        cout << "You will need to enter a series of values for the program to proceed." << endl;

        double cutoff,binr, bintheta;
        cout << "Please enter a cutoff to build the g(r) neighbor list for actin:\n>";
        cin >> cutoff;
	cout <<"Please enter a bin size for r:\n>";
	cin >> binr;
        cout <<"Please enter a bin size for theta in degree:\n>";
        cin >> bintheta;

	int rmax=int(cutoff/binr);
        int tmax=int(180/bintheta);
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
		double gr[50][180]={0};
		double grr[50][180][5000]={0};
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
		int total_num =0;
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
		   int ajID=100;
                   double ajx, ajy, aix, aiy;
                   double theta=0;
		//int imax=0, n=0;
		//build the list of nearest neighbour 
		 for(int i=0; i<atoms; i++){
                        xi = actin[i][3];
                        yi = actin[i][4];
			aix=actin[i][5];
                        aiy=actin[i][6];
			
			//int imax=0;
                        for(int j=0; j<atoms;j++){
                                if(j==i) {continue;}
                                xj = actin[j][3];
                                yj = actin[j][4];
                                dx=xj-xi;
                                dy=yj-yi;
				dij=sqrt(dx*dx+dy*dy);
				ajx=actin[ajID][5];
                                ajy=actin[ajID][6];
                                if(dij>cutoff) {continue;}
			        theta= acos((aix*ajx+aiy*ajy)/(sqrt(aix*aix+aiy*aiy)*sqrt(ajx*ajx+ajy*ajy)))*180.0/PI;;  
                           //     double tmp=0;
				//for( n=0; n<20;n++){
                                  //      if(tmp<neighbor[1][n][i]){
                                   //             tmp=neighbor[1][n][i];
                                    //            imax=n;
                                     //           }
                                      //  }
                                //if(dij>neighbor[1][imax][i]) {continue;}
				//else{
				int m=0,n=0;
				n = int(floor(dij/binr));
				m = int(floor(theta/bintheta));
				//cout<<theta<<endl;
				//cout<<bintheta<<endl;
				//cout << m<< endl;
				total_num++;
				gr[n][m]++;
				
                                //neighbor[1][imax][i]=dij;
                                 //       neighbor[0][imax][i]=j;
                                //        }
                             //   cout<< i << " " <<j<<endl;
				//        imax++;
                                }
				//if(imax!=0)
				//{actin[i][7]=imax;
			//	cout << i << " " << imax << endl;
				//}
				//else
				//actin[i][7]=0;
                        }// end of count gr[m][n]
		cout<<total_num << endl;
//calculate the q6 order 
			
		     for(i=0; i< rmax; i++){
			 for(j=0; j< tmax; j++){
				double bint,tmp,tmp1;
				
				bint = bintheta/180*2*PI;
				tmp = gr[i][j]/total_num*200/25;
                                tmp1 = tmp/(i*binr*binr)/bint;
				grr[i][j][counter]=gr[i][j];
			//	output << i*binr << " "<< j*bintheta  <<" "<< tmp1 << endl;
		}}


}
                                           for(i=0; i< rmax; i++){
                         for(j=0; j< tmax; j++){
                         double tmp=0,tmp1=0;
			 for(int k=1; k< counter+1; k++)
			{ tmp+=grr[i][j][k];}
		         tmp1= tmp/counter;	
			 output << i*binr << " "<< j*bintheta  <<" "<< tmp1 << endl;
			}}


}
 
