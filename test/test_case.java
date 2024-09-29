import java.util.HashMap;

class Teacher {
    String name;
}

class Student {
    String name;
    int age;
    double[] scores = new double[3];
    HashMap<String, String> myMap = new HashMap<String, String>();

    public void hello(Teacher teacher) {
        System.out.println("Hello! teacher " + teacher.name);
    }

    public void hello(Student student) {
        System.out.println("Hello! student " + student.name);
    }

    public String propagate(Student student) {
        System.out.println(student);
        hello(student);
        hello(student);
        return student.name;
    }
}

public class test_case {
    public static void main(String[] args) {
        Student s1 = new Student();
        s1.name = "cpg2stmt";
        Student s2 = s1;
        s1.age = 24;
        String s2name = s2.name;
        System.out.println(s2name);
        System.out.println(s2.age);
        String ret = s2.propagate(s2);
        System.out.println(ret);
        Student s3 = new Student();
        s3.name = "AAA";
        Teacher t1 = new Teacher();
        t1.name = "BBB";
        s1.hello(s3);
        s1.hello(t1);
        String name = s1.name;
        String name1 = name;
        if (name == "cpg2stmt") {
            System.out.println("s1.name == cpg2stmt");
        } else {
            System.out.println("s1.name != cpg2stmt");
        }
        String new_name = name1 = name = "test";
        System.out.println(new_name);
        int x = 10;
        int y = 20;
        int z = x + y;
        int p = x + y + z;
        System.out.println(p);
        s1.scores[0] = 98;
        System.out.println("Math Score:" + s1.scores[0]);
        s1.myMap.put("category", "XSS");
        System.out.println("category parameter:" + s1.myMap.get("category"));
        double[] myList = new double[x];
        myList[0] = 5.6;
        double first = myList[0];
        boolean flag = s1.age > 18 ? true : false;
        if (flag) {
            System.out.println(s1.name + " Age > 18");
        }
        new_name = name1.concat(name);
        System.out.println(new_name);
        int j = 1;
        while (j <= 5) {
            System.out.println(j);
            j++;
        }
        int day = 3;
        switch (day) {
            case 1:
                System.out.println("Monday");
                break;
            case 2:
                System.out.println("Tuesday");
                break;
            case 3:
                System.out.println("Wednesday");
                break;
            default:
                System.out.println("Invalid day");
        }
        if (day == 1) {
            System.out.println("Monday");
        } else if (day == 2) {
            System.out.println("Tuesday");
        } else if (day == 3) {
            System.out.println("Wednesday");
        } else {
            System.out.println("Error");
            int q = 10;
            int w = 20;
            int e = 30;
        }
    }
}