//#include <stdio.h>
//
//int main()
//{
//    char correct, current;
//    long long beforeTimeStamp, afterTimeStamp = 0;
//    int currentCombo = 0, maxCombo = 0;
//    int count = 1;
//    while (count <= 2010)
//    {
//        scanf(" %c %c %lld", &correct, &current, &beforeTimeStamp);
//        if (correct == current)
//        {
//            if (beforeTimeStamp - afterTimeStamp <= 1000)
//            {
//                currentCombo++;
//            }
//            else
//            {
//                currentCombo = 1;
//            }
//        }
//        else
//        {
//            currentCombo = 0;
//        }
//        if (maxCombo < currentCombo)
//        {
//            maxCombo = currentCombo;
//        }
//        afterTimeStamp = beforeTimeStamp;
//        count++;
//    }
//    printf("%d\n", maxCombo);
//    return 0;
//}