.class abstract LP/h;
.super LP/g;
.source "SourceFile"


# direct methods
.method public static b()Ljava/util/List;
    .locals 1

    .line 1
    sget-object v0, LP/r;->a:LP/r;

    .line 2
    .line 3
    return-object v0
.end method

.method public static final c()V
    .locals 2

    .line 1
    new-instance v0, Ljava/lang/ArithmeticException;

    .line 2
    .line 3
    const-string v1, "Index overflow has happened."

    .line 4
    .line 5
    invoke-direct {v0, v1}, Ljava/lang/ArithmeticException;-><init>(Ljava/lang/String;)V

    .line 6
    .line 7
    .line 8
    throw v0
.end method
